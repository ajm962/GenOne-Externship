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
#import RPI.GPIO as GPIO

#GPIO.setmode(GPIO.BOARD)
#GPIO.setup(16, GPIO.IN)
#GPIO.setup(12, GPIO.IN)
camera = PiCamera()
rawCapture = PiRGBArray(camera)
time.sleep(0.1)


### Baseline functions which create list of employees & entry log based on status of office
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

def updating_log():
  """
  Updates employee status dictionary based on who is entering/exitting the office
  """
  upd_log = default_log() # initialize

  if: # front cam sees face --> dict @ person's name changes to "in office"
    upd_log[name] = "in office"
  elif: # outside cam sees square big enough to constitute leaving --> dict updates person as "out of office"
    upd_log[name] = "out of office"
  elif: # lights out
    upd_log = default_log()

  return upd_log
   
def build_table():
  entry_log = update_log()
  log_keys = list(entry_log.keys())
  log_vals = list(entry_log.values())

  t = PrettyTable(['Employee', 'Status'])
  for i in range(len(entry_log)):
    t.add_row([log_keys[i],log_vals[i]])
  return t


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
  for i in range(0,150): # change 150 to fit needs
    motor.clockwise()
  l293d.cleanup()

def lock():
  """
  Given info from lock_state(), controls servomotor and lock deadbolt
  """
  motor = l293d.motor(0,0,0) # input pins the motor uses
  for i in range(0,150): # change 150 to fit needs
    motor.counterclockwise()
  l293d.cleanup()


### Facial detection foundational controls
def faces():
  """
  Takes in video footage from computer and uses facial detection to put square around people
  """
  pass 

def faces_train():
  """
  Using faces function, looks at detected faces and tries to recognize/classify them
  returns boolean regarding if face is recognized
  """
  face_cascade = cv2.CascadeClassifier('/Users/anna/Desktop/GenOne/cascades/data/haarcascade_frontalface_default.xml')
  recognizer = cv2.face.LBPHFaceRecognizer_create()
  y_labels = [] # some number
  x_train = [] # grayscale numpy array
  label_ids = get_employees()

  for dirpath, dirnames, files in os.walk(image_path()):
    for file in files:
      if file.endswith("png") or file.endswith("jpg"):
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
  pass

def office_camera():
  pass


### At end of day, functions detect last employee leaving and final lock
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




