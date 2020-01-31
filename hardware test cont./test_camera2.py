from imutils.video import VideoStream
from imutils.video import FPS
import face_recognition
import argparse
import imutils
import pickle
import time
import cv2

# construct the argument parser and parse the arguments
#ap = argparse.ArgumentParser()
#ap.add_argument("-c", "--cascade", required=True, help = "path to where the face cascade resides")
#ap.add_argument("-e", "--encodings", required=True, help="path to serialized db of facial encodings")
#args = vars(ap.parse_args())
args = {'cascade': '/home/pi/Desktop/GenOne-Externship/haarcascade_frontalface_default.xml', 'encodings': '/home/pi/Desktop/GenOne-Externship/encodings.pickle'}

# load the known faces & embeddings along with OpenCV's Haarcascade for face detection
print("[INFO] loading encodings + face detector...")
data = pickle.loads(open(args["encodings"], "rb").read())
detector = cv2.CascadeClassifier(args["cascade"])

# initialize the video stream and allow the camera sensor to warm up
print("[INFO] starting video stream...")
vs = VideoStream(usePiCamera=True).start() #-> for when connected
time.sleep(2.0)

# start the FPS counter
fps = FPS().start()

# loop over frames from the video file stream
while True:
    # grab the frame from the threaded video stream & resize it to 500px (to speedup processing)
    frame = vs.read()
    frame = imutils.resize(frame, width=500)
    
    # convert the input frame to grayscale (face detection) and from BGR to RGB (face recognition), detect faces
    roi_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    roi_color = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    faces = detector.detectMultiScale(roi_gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30), flags=cv2.CASCADE_SCALE_IMAGE)

    # box coordinates in (x, y, w, h), need (top, right, bottom, left) order --> reorder
    boxes = [(y, x + w, y + h, x) for (x, y, w, h) in faces]
    encodings = face_recognition.face_encodings(roi_color, boxes)   # compute  facial embeddings for each face bounding box
    names = []

    for face in encodings:
        matches = face_recognition.compare_faces(data["encodings"], face) # attempt to match each face in the input image to encodings
        name = "Unknown"

        # check if found a match
        if True in matches:
            # find the indexes of all matched faces
            matchedIdxs = [i for (i, b) in enumerate(matches) if b]
            # initialize dictionary to count # times face was matched
            counts = {}

            # loop over matched indexes and maintain count for face
            for i in matchedIdxs:
                name = data["names"][i]
                counts[name] = counts.get(name, 0) + 1
            name = max(counts, key=counts.get) # determine recognized face w/ most votes

        names.append(name)
        print(names)

    for ((top, right, bottom, left), name) in zip(boxes, names):    # loop over the recognized faces
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        y = top - 15 if top - 15 > 15 else top + 15
        cv2.putText(frame, name, (left, y), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2) # write predicted name on the image

    cv2.imshow("Frame", frame) # display image to our screen
    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"): # if the `q` key was pressed, break from the loop
        break

    # update the FPS counter
    fps.update()

# stop the timer and display FPS information
fps.stop()
print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))

cv2.destroyAllWindows()
vs.stop()
