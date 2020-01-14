import os 
import cv2 
import numpy as np 
import tkinter as tk
import time
from PIL import Image 
import pickle 
from prettytable import PrettyTable
import matplotlib.pyplot as plt
import l293d.driver as l293d
from picamera import PiCamera
import RPI.GPIO as GPIO

GPIO.setmode(GPIO.BOARD)
GPIO.setup(16, GPIO.IN)
GPIO.setup(12, GPIO.IN)
camera = PiCamera()
rawCapture = PiRGBArray(camera)
time.sleep(0.1)


### Baseline functions which create list of employees & preliminary log based on status of office
def image_path():
  """ 
  returns path to folder of images
  """
  BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # os.path.dirname returns directory name of path to file
  image_dir = os.path.join(BASE_DIR, "images") # path to folder inside GenOne called "images"
  return image_dir

def get_employees():
  """
  Returns list of all employees permitted in office based on provided images
  Baseline state = all are out of office
  """
  label_ids = []
  for dirpath, dirnames, files in os.walk(image_path()): # generates tuple w/ filenames
    for file in files: # look through each image in folder
      if file.endswith("png") or file.endswith("jpg"): # if file found is viable image...
        name = os.path.basename(dirpath).replace(" ", "_").lower() # gives back folder name
        if name not in label_ids:
          label_ids.append(name)

  return label_ids 

def id_dict():
  current_id = 0
  label_ids = {}
  names = get_employees()
  for name in names:
    label_ids[name] = current_id
    current_id += 1
  return label_ids
  
def default_log():
  """
  Returns dictionary logging all employees out of office
  """
  emp_lis = get_employees() # log of employees w/ id numbers
  def_log = {} # new dic for table entries

  for val in emp_lis:
    name = val.replace("_", " ")
    def_log[name] = "out of office"

  return def_log


### Check for states of lock and door; control servomotor to change lock state if door is closed
def lock_state():
  """
  Tells RPI whether deadbolt is in locked or unlocked position
  unlocked = True
  locked = False
  """
  if GPIO.input(16) == 1:
    return True
  else:
    return False
  GPIO.cleanup()

def door_state():
  """
  Reads whether door is open or closed based on info from limit switches
  open = True
  closed = False
  """
  if GPIO.input(16)==1:
    return True
  else:
    return False
  GPIO.cleanup()

def unlock():
  """
  Given info from lock_state(), controls servomotor and unlock deadbolt
  """
  motor = l293d.motor(0,0,0) # input pins the motor uses
  for i in range(0,90): # change 150 to fit needs
    motor.clockwise()
  l293d.cleanup()

def lock():
  """
  Given info from lock_state(), controls servomotor and lock deadbolt
  """
  motor = l293d.motor(0,0,0) # input pins the motor uses
  for i in range(0,90): # change 150 to fit needs
    motor.counterclockwise()
  l293d.cleanup()


### Facial detection foundational controls
def faces_train():
  """
  Using faces function, looks at detected faces and tries to recognize/classify them
  returns boolean regarding if face is recognized
  """
  face_cascade = cv2.CascadeClassifier('/Users/anna/Desktop/GenOne/cascades/data/haarcascade_frontalface_default.xml')
  recognizer = cv2.face.LBPHFaceRecognizer_create()
  y_labels = [] # some number
  x_train = [] # grayscale numpy array
  label_ids = id_dict()

  for dirpath, dirnames, files in os.walk(image_path()):
    for file in files:
      if file.endswith("png") or file.endswith("jpg"):
        path = os.path.join(dirpath, file) # join path of folder w/ specific image
        label = os.path.basename(dirpath).replace(" ", "_").lower() # gives back folder name

        pil_image = Image.open(path).convert("L") # grayscale
        size = (550, 550)
        final_image = pil_image.resize(size, Image.ANTIALIAS)
        image_array = np.array(final_image, "uint8") # convert image to numpy array (unint8 = unsigned 8 bit integer)

        faces = face_cascade.detectMultiScale(image_array, scaleFactor = 1.5, minNeighbors = 5) # find face(s)
        for (x, y, w, h) in faces:
          roi = image_array[y:y + h, x:x + w] # get numpy array for region face is in
          x_train.append(roi)
          y_labels.append(label_ids[label]) # assign num to name

  with open("labels.pickle", 'wb') as f:
    pickle.dump(label_ids, f)

  recognizer.train(x_train, np.array(y_labels))
  recognizer.save("trainer.yml")


### Camera state controls
def hall_camera():
  """
  Takes in video footage from hallway cam and uses facial detection to distinguish people
  """
  front_cascade = cv2.CascadeClassifier('/Users/anna/Desktop/GenOne/cascades/data/haarcascade_frontalface_default.xml')
  recognizer = cv2.face.LBPHFaceRecognizer_create()
  recognizer.read("trainer.yml")
  cap = cv2.VideoCapture(0) # change this to access camera of RPI

  labels = {}
  with open("labels.pickle", 'rb') as f: # gives label dictionary
      og_labels = pickle.load(f)
      labels = {v:k for k,v in og_labels.items()} # reverse order of dict

  # Capture frame-by-frame
  ret, frame = cap.read()
  gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
  faces = front_cascade.detectMultiScale(gray, scaleFactor = 1.5, minNeighbors = 5)

  for (x, y, w, h) in faces:
    color = (0, 255, 0)
    stroke = 2
    cv2.rectangle(frame, (x, y), (x + w, y + h), color, stroke)
    
    # cropped squares of faces
    roi_gray = gray[y:y + h, x:x + w]

    # recognize region of interest
    id_, conf = recognizer.predict(roi_gray)
    if conf >= 45 and conf <= 50:
      font = cv2.FONT_HERSHEY_SIMPLEX
      cv2.putText(frame, labels[id_], (x, y), font, 1, (255, 255, 255), 2, cv2.LINE_AA)
      name = labels[id_].replace("_", " ")
      return name

def office_camera():
  """
  Takes in video footage from inside camera and uses facial detection to detect people
  """
  front_cascade = cv2.CascadeClassifier('/Users/anna/Desktop/GenOne/cascades/data/haarcascade_frontalface_default.xml')
  recognizer = cv2.face.LBPHFaceRecognizer_create()
  recognizer.read("trainer.yml")
  cap = cv2.VideoCapture(0) # change to access inside camera

  labels = {}
  with open("labels.pickle", 'rb') as f: # gives label dictionary
      og_labels = pickle.load(f)
      labels = {v:k for k,v in og_labels.items()} # reverse order of dict

  # Capture frame-by-frame
  ret, frame = cap.read()
  gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
  faces = front_cascade.detectMultiScale(gray, scaleFactor = 1.5, minNeighbors = 5)

  for (x, y, w, h) in faces:
    color = (0, 255, 0)
    stroke = 2
    cv2.rectangle(frame, (x, y), (x + w, y + h), color, stroke)

    # condition to see if box is big enough to consitute person leaving
    if w >= 300 and h>= 300:
      is_leaving = True
    else:
      is_leaving = False
    
    # cropped squares of faces
    roi_gray = gray[y:y + h, x:x + w]

    # recognize region of interest
    id_, conf = recognizer.predict(roi_gray)
    if conf >= 45 and conf <= 50:
      font = cv2.FONT_HERSHEY_SIMPLEX
      cv2.putText(frame, labels[id_], (x, y), font, 1, (255, 255, 255), 2, cv2.LINE_AA)
      name = labels[id_].replace("_", " ")
      return (name, is_leaving)


### Throughout day, log updates; at end of day, functions detect last employee leaving and final lock
def updating_log():
  """
  Updates employee status dictionary based on who is entering/exitting the office
  """
  if hall_camera() != None:
    default_log()[str(hall_camera())] = "in office"
  elif office_camera()[1]:
    default_log()[str(office_camera()[0])] = "out of office"
  elif lights():
    default_log() = default_log()

  return upd_log
   
def build_table():
  entry_log = updating_log()
  log_keys = list(entry_log.keys())
  log_vals = list(entry_log.values())

  t = PrettyTable(['Employee', 'Status'])
  for i in range(len(entry_log)):
    t.add_row([log_keys[i],log_vals[i]])
  return t

def lights():
  """
  Detects whether or not last person has turned off the lights before leaving
  Returns True if lights are off
  """
  camera.capture(rawCapture, format="rgb")
  iamge = rawCapture.array
  black_thresh = 75 # 0 = pitch black, 255 = bright white
  if image < black_thresh:
    return True
  else:
    return False


#########################
# turn on RPI
# start server
# initialize main code?
#########################

faces_train()
log = default_log()

while(True):
  # check door state
  if door_state(): # open
    if not lock_state(): # locked
      unlock()
  if not door_state(): # closed
    # check entry log
    # no people then lock door
    # people do nothing

  # check outside camera
  if hall_camera() != None: # if camera detects a recognized face
    name = hall_camera()
    if not door_state():
      if not lock_state()
        unlock()
    updating_log()

  # check entry log
  if default_log() != updating_log():
    if lights(): # dark
      time.sleep(30)
      lock()
      updating_log()
    if not lights(): # lights on
      if office_camera() != None: # detects face
        if office_camera()[1]:
          unlock()




