# USAGE
# When encoding on laptop, desktop, or GPU (slower, more accurate):
# python3 encode_faces.py --dataset dataset --encodings encodings.pickle --detection-method cnn
# When encoding on Raspberry Pi (faster, more accurate):
# python3 encode_faces.py --dataset dataset --encodings encodings.pickle --detection-method hog

# import the necessary packages
from imutils import paths
import face_recognition
import argparse
import pickle
import cv2
import os

# construct the argument parser and parse the arguments
#ap = argparse.ArgumentParser()
#ap.add_argument("-i", "--dataset", required = True, help = "path to input directory of faces + images")
#ap.add_argument("-e", "--encodings", required = True, help = "path to serialized db of facial encodings")
#ap.add_argument("-d", "--detection-method", type=str, help = "either `hog` or `cnn`", default = "cnn")
#args = vars(ap.parse_args())

args = {'dataset': '/Users/anna/Desktop/deep-learning/dataset', 'encodings': '/Users/anna/Desktop/deep-learning/encodings.pickle', 'detection_method': 'cnn'}

# grab the paths to the input images in our dataset
print("[INFO] quantifying faces...")
imagePaths = list(paths.list_images(args["dataset"]))
knownEncodings = []
knownNames = []

for (i, imagePath) in enumerate(imagePaths): # loop over each image in dataset
	
	print("[INFO] processing image {}/{}".format(i + 1, len(imagePaths)))
	name = imagePath.split(os.path.sep)[-2] # extract the person name from the image path
	image = cv2.imread(imagePath)
	rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB) 	# convert input image from RGB (OpenCV ordering)
	boxes = face_recognition.face_locations(rgb, model = args["detection_method"]) 	# detect coordinates of box around face in image
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
