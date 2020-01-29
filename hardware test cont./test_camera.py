"""
test a single image
"""
# import the necessary packages
from picamera.array import PiRGBArray
from picamera import PiCamera
import time
import cv2
 
# # initialize the camera and grab a reference to the raw camera capture
# camera = PiCamera()
# rawCapture = PiRGBArray(camera)
#  
# # allow the camera to warmup
# time.sleep(0.1)
#  
# # grab an image from the camera
# camera.capture(rawCapture, format="bgr")
# image = rawCapture.array
#  
# # display the image on screen and wait for a keypress
# cv2.imshow("Image", image)
# cv2.waitKey(0)

# cd to folder and print python3 test_image.py in terminal



"""
test livestream
"""
# import the necessary packages
#from picamera.array import PiRGBArray
#from picamera import PiCamera
#import time
#import cv2
 
##initialize the camera and grab a reference to the raw camera capture
camera = PiCamera()
camera.resolution = (640, 480)
camera.framerate = 32
rawCapture = PiRGBArray(camera, size=(640, 480))
 
##allow the camera to warmup
time.sleep(0.1)
 
##capture frames from the camera
for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
    # grab the raw NumPy array representing the image, then initialize the timestamp
    # and occupied/unoccupied text
    image = frame.array
 
    # show the frame
    cv2.imshow("Frame", image)
    key = cv2.waitKey(1) & 0xFF
 
    # clear the stream in preparation for the next frame
    rawCapture.truncate(0)
 
    # if the `q` key was pressed, break from the loop
    if key == ord("q"):
       break