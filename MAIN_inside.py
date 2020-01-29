import os 
import face_recognition
import dropbox
import cv2 
import time
import pickle 
import wiringpi
import imutils
import serial
from imutils import paths
from datetime import datetime
from imutils.video import VideoStream
from prettytable import PrettyTable
from PIL import Image
import RPi.GPIO as GPIO
import threading
import concurrent.futures
import dropbox
from dropbox.files import WriteMode

# turn on RPI, start server
camera = VideoStream(usePiCamera=True).start()
time.sleep(2.0)
wiringpi.wiringPiSetupGpio()
serial_flag = True
entering_names = []

### Baseline functions which create list of employees & preliminary log based on status of office
def image_path():
  """ 
  returns path to folder of images
  """
  BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # os.path.dirname returns directory name of path to file
  image_dir = os.path.join(BASE_DIR, "dataset") # path to folder inside GenOne called "images"
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


### Check for states of lock and door; control servomotor to change lock state if door is closed
def init_pins():
  wiringpi.pinMode(18, wiringpi.GPIO.PWM_OUTPUT) # set up pins
  wiringpi.pinMode(16, wiringpi.GPIO.INPUT) 
  wiringpi.pinMode(25, wiringpi.GPIO.INPUT)
  wiringpi.pinMode(20, wiringpi.GPIO.INPUT)
  wiringpi.pwmSetMode(wiringpi.GPIO.PWM_MODE_MS) # set the PWM mode to milliseconds
  wiringpi.pwmSetClock(190) # divide down clock
  wiringpi.pwmSetRange(150)

def lock_state(): # 16&25 control sensors surrounding lock
  """
  Tells RPI whether deadbolt is in locked or unlocked position
  unlocked = True
  locked = False
  """
  if (wiringpi.digitalRead(16) == 0): # blue pressed, unlocked
    return True
  elif (wiringpi.digitalRead(25) == 0): # green pressed, locked
    return False

def door_state():
  """
  Reads whether door is open or closed based on info from limit switches
  open = True
  closed = False
  """
  if (wiringpi.digitalRead(20) == 0):
    return True
  else:
    return False

def unlock():
  """
  Given info from lock_state(), controls servomotor and unlock deadbolt
  """
  for pulse in range(0, 300, 1): # counterclockwise
    wiringpi.pwmWrite(18, pulse)
    time.sleep(.0004)

def lock():
  """
  Given info from lock_state(), controls servomotor and lock deadbolt
  """
  for pulse in range(300, 0, -1): # clockwise
    wiringpi.pwmWrite(18, pulse)
    time.sleep(.0004)  


### Facial detection foundational controls
def faces_train():
  """
  Using faces function, looks at detected faces and tries to recognize/classify them
  returns boolean regarding if face is recognized
  """
  args = {'dataset': '/home/pi/Desktop/GenOne-Externship/dataset', 'encodings': '/home/pi/Desktop/GenOne-Externship/encodings.pickle', 'detection_method': 'hog'}

  # grab the paths to the input images in our dataset
  print("[INFO] quantifying faces...")
  imagePaths = list(paths.list_images(args["dataset"]))
  knownEncodings = []
  knownNames = []

  for (i, imagePath) in enumerate(imagePaths): # loop over each image in dataset
    
    print("[INFO] processing image {}/{}".format(i + 1, len(imagePaths)))
    name = imagePath.split(os.path.sep)[-2] # extract the person name from the image path
    image = cv2.imread(imagePath)
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)    # convert input image from RGB (OpenCV ordering)
    boxes = face_recognition.face_locations(rgb, model = args["detection_method"])  # detect coordinates of box around face in image
    encodings = face_recognition.face_encodings(rgb, boxes) # compute the facial embedding for the face

    for encoding in encodings:
      # add each encoding + name to our set of known names and
      knownEncodings.append(encoding)
      knownNames.append(name)

  # dump the facial encodings + names to disk
  print("[INFO] serializing encodings...")
  data = {"encodings": knownEncodings, "names": knownNames}
  f = open(args["encodings"], "wb")
  f.write(pickle.dumps(data))
  f.close()


### Camera state controls
def office_camera():
  """
  Takes in video footage from inside camera and uses facial detection to detect people
  """
  args = {'cascade': '/home/pi/Desktop/GenOne-Externship/haarcascade_frontalface_default.xml', 'encodings': '/home/pi/Desktop/GenOne-Externship/encodings.pickle'}

  # load the known faces & embeddings along with OpenCV's Haarcascade for face detection
  data = pickle.loads(open(args["encodings"], "rb").read())
  detector = cv2.CascadeClassifier(args["cascade"])

  frame = camera.read()
  frame = imutils.resize(frame, width=500)
  roi_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
  roi_color = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
  
  room_snapshot = "light-test.png" 
  cv2.imwrite(room_snapshot, roi_gray)
  
  faces = detector.detectMultiScale(roi_gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30), flags=cv2.CASCADE_SCALE_IMAGE)

  # box coordinates in (x, y, w, h), need (top, right, bottom, left) order --> reorder
  boxes = [(y, x + w, y + h, x) for (x, y, w, h) in faces]
  encodings = face_recognition.face_encodings(roi_color, boxes) # compute facial embeddings for each face bounding box
  names = [] # list of detected faces in office
  leaving = [] # list of people in office close enough to door to be leaving
  
  for face in encodings:
    matches = face_recognition.compare_faces(data["encodings"], face) # attempt to match each face in the input image to encodings
    name = "Unknown"

    if True in matches:
      matchedIdxs = [i for (i, b) in enumerate(matches) if b]
      counts = {}
      for i in matchedIdxs:
        name = data["names"][i]
        counts[name] = counts.get(name, 0) + 1
      name = max(counts, key=counts.get) # determine recognized face w/ most votes  :
      if counts[name] > 3:
        names.append(name) # add name to list of people in view if within threshold

    for ((top, right, bottom, left), name) in zip(boxes, names): # loop over the recognized faces
      if abs(right - left) >= 65:
        leaving.append(name)

  if len(leaving) > 0:
    return leaving
  else:
    return None

  
### Throughout day, log updates; at end of day, functions detect last employee leaving and final lock
def build_table(entry_log):
  now = datetime.now()
  log_keys = list(entry_log.keys())
  log_vals = list(entry_log.values())
  dbx = dropbox.Dropbox("AzJy55j2JKAAAAAAAAAAEblAFF2UcphRfzAoGeSrJxqToDlipWKHrVnOSN4hz9CA")

  t = PrettyTable(['Employee', 'Status'])
  for i in range(len(entry_log)):
    t.add_row([log_keys[i],log_vals[i]])
  t = t.get_string()

  dt = now.strftime("%m/%d/%Y %H:%M:%S")
  f = open("log.txt", 'w')
  f.truncate(0)
  f.write("Latest Update: " + str(dt) + "\n" + t)
  f.close()
  
  with open("/home/pi/Desktop/GenOne-Externship/log.txt", "rb") as f2:
    dbx.files_upload(f2.read(), '/log.txt', mute = True, mode = WriteMode('overwrite'))
  f2.close()

def lights():
  """
  Detects whether or not last person has turned off the lights before leaving
  Returns True if lights are off
  """
  im = Image.open('light-test.png')
  pixels = im.getdata()   # get the pixels as a flattened sequence
  black_thresh = 50 # darker the pixel, lower the value
  tot_pixels = 0
  n = len(pixels)

  for pixel in pixels:
    tot_pixels += pixel
    
  if (tot_pixels/n) < black_thresh: # get average value of pixels
    return True
  else:
    return False


### Serial communication
def receive_rec():
  """
  Recieves names from outside camera if recognizable faces are detected
  """
  global entering_names
  global serial_flag
  
  while(True):
      if serial_flag:
          ser = serial.Serial("/dev/ttyS0", 9600)
          encoding = "utf-8"
          receive = ""
          
          byte = ser.readline()
          receive += str(byte, encoding) # bytes to string
          names = receive.split(',') # create list of names received
          
          ser.close()
          entering_names = names
          serial_flag = False


"""
MAIN CODE! RUNNING FUNCTIONS! YES!
"""
t1 = threading.Thread(target = receive_rec)
t1.start()
  
#faces_train()
log_main = default_log()
build_table(log_main)
init_pins()

while(True):
    inside = office_camera()
    lock = lock_state()
    door = door_state()
    
   # check door state
    if door == True: # open
        if lock == False: # locked
            unlock()
    if door == False: # closed
        if lock == True and log_main == default_log(): # unlocked & office empty
            lock()
 
   # check outside camera
    if serial_flag == False: # if camera detects a recognized face
        names = entering_names
        if door == False:
            if lock == False:
                unlock()
        for name in names:
            name = name.replace("\n", "")
            if name in log_main.keys():
                log_main[name] = "in office"
        build_table(log_main)
        serial_flag = True

  # check entry log
    if log_main != default_log():
        if lights == True: # dark
            time.sleep(30)
            lock()
            log_main = default_log()
            build_table(log_main)
        else: # lights on
            if inside is not None: # if detects face
                if lock == False:
                    unlock()
                for name in inside:
                    log_main[name] = "out of office"
                build_table(log_main)
            