import face_recognition
import os
import cv2 
import pickle
import time
import imutils
from imutils.video import VideoStream
from imutils import paths
import serial

camera = VideoStream(usePiCamera=True).start()
time.sleep(2.0)

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
def hall_camera():
  """
  Takes in video footage from hallway cam and uses facial detection to distinguish people
  """
  args = {'cascade': '/home/pi/Desktop/GenOne-Externship/haarcascade_frontalface_default.xml', 'encodings': '/home/pi/Desktop/GenOne-Externship/encodings.pickle'}

  # load the known faces & embeddings along with OpenCV's Haarcascade for face detection
  data = pickle.loads(open(args["encodings"], "rb").read())
  detector = cv2.CascadeClassifier(args["cascade"])
  
  frame = camera.read()
  frame = imutils.resize(frame, width=500)
  
  roi_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
  roi_color = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
  faces = detector.detectMultiScale(roi_gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30), flags=cv2.CASCADE_SCALE_IMAGE)

  # box coordinates in (x, y, w, h), need (top, right, bottom, left) order --> reorder
  boxes = [(y, x + w, y + h, x) for (x, y, w, h) in faces]
  encodings = face_recognition.face_encodings(roi_color, boxes) # compute facial embeddings for each face bounding box
  names = []

  for face in encodings:
    matches = face_recognition.compare_faces(data["encodings"], face) # attempt to match each face in the input image to encodings
    name = "Unknown"
    
    if True in matches:
      matchedIdxs = [i for (i, b) in enumerate(matches) if b]
      counts = {}
      for i in matchedIdxs:
        name = data["names"][i]
        counts[name] = counts.get(name, 0) + 1
      name = max(counts, key=counts.get) # determine recognized face w/ most votes
      if counts[name] > 3:
          names.append(name)
          
  if len(names) > 0:
    return names
  else:
    return None

def serial_send(names):
  """
  Send inside RPI information about faces detected in hallway
  """
  ser = serial.Serial('/dev/ttyS0',9600)
  encoded = (",".join(names[0:len(names)])+"\n").encode()
  ser.write(encoded)
  ser.close()

"""
MAIN! CODE!
"""

#faces_train()
while(True):
  names = hall_camera()
  if names is not None:
      serial_send(names) # send message to other RPI

