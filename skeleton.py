import os 
import cv2 
import numpy as np 
from PIL import Image 
import pickle 
from prettytable import PrettyTable
import matplotlib.pyplot as plt
#import RPI.GPIO as GPIO

#GPIO.setmode(GPIO.BOARD)
#GPIO.setup(16, GPIO.IN)
#GPIO.setup(12, GPIO.IN)

def lock_state():
  """
  Tells RPI whether deadbolt is in locked or unlocked position
  unlocked = True
  locked = False
  """
  if GPIO.input(16) == 0:
    return True
  else:
    return False
  GPIO.cleanup()

def change_lock():
  """
  Given info from lock_state(), controls servomotor and changes state of deadbolt
  """

def door_state():
  """
  Reads whether door is open or closed based on info from limit switches
  open = True
  closed = False
  """
  if GPIO.input(16)==0:
    return True
  else:
    return False
  GPIO.cleanup()

def get_employees():
  """
  returns dictionary of all employees permitted in office based on provided images
  """
  BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # os.path.dirname returns directory name of path to file
  image_dir = os.path.join(BASE_DIR, "images") # path to folder inside GenOne called "images"
  
  label_ids = {}
  current_id = 1
  for dirpath, dirnames, files in os.walk(image_dir): # generates tuple w/ filenames
    for file in files: # look through each image in folder
      if file.endswith("png") or file.endswith("jpg"): # if file found is viable image...
        label = os.path.basename(dirpath).replace(" ", "_").lower() # gives back folder name
        if label not in label_ids:
          label_ids[label] = current_id
          current_id += 1

  
  return label_ids  

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
  BASE_DIR = os.path.dirname(os.path.abspath(__file__))
  image_dir = os.path.join(BASE_DIR, "images")
  face_cascade = cv2.CascadeClassifier('/Users/anna/Desktop/GenOne/cascades/data/haarcascade_frontalface_default.xml')
  recognizer = cv2.face.LBPHFaceRecognizer_create()
  y_labels = [] # some number
  x_train = [] # grayscale numpy array
  label_ids = get_employees()

  for dirpath, dirnames, files in os.walk(image_dir):
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

def hall_camera():
  pass

def office_camera():
  pass

def entry_log():
  id_log = get_employees() # log of employees w/ id numbers
  entry_log = {} # new dic for table entries

  for key in id_log:
    name = key.replace("_", " ")
    entry_log[name] = "out of office"

  log_keys = list(entry_log.keys())
  log_vals = list(entry_log.values())

  t = PrettyTable(['Employee', 'Status'])
  for i in range(len(entry_log)):
    t.add_row([log_keys[i],log_vals[i]])
  return t

print(entry_log())
print(get_employees())

