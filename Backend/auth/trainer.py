import cv2
import numpy as np
from PIL import Image #pillow package
import os

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

path = os.path.join(script_dir, 'samples') # Path for samples already taken

recognizer = cv2.face.LBPHFaceRecognizer_create() # Local Binary Patterns Histograms

# Try to load cascade classifier
cascade_path = os.path.join(script_dir, 'haarcascade_frontalface_default.xml')

# Check if local file exists, if not use OpenCV's built-in
if not os.path.exists(cascade_path):
    print("⚠️  Local cascade file not found, using OpenCV built-in...")
    cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'

if not os.path.exists(cascade_path):
    print("❌ Error: Cascade file not found!")
    exit(1)

detector = cv2.CascadeClassifier(cascade_path)

if detector.empty():
    print("❌ Error: Could not load cascade classifier!")
    exit(1)


def Images_And_Labels(path): # function to fetch the images and labels

    imagePaths = [os.path.join(path,f) for f in os.listdir(path)]     
    faceSamples=[]
    ids = []

    for imagePath in imagePaths: # to iterate particular image path

        gray_img = Image.open(imagePath).convert('L') # convert it to grayscale
        img_arr = np.array(gray_img,'uint8') #creating an array

        id = int(os.path.split(imagePath)[-1].split(".")[1])
        faces = detector.detectMultiScale(img_arr)

        for (x,y,w,h) in faces:
            faceSamples.append(img_arr[y:y+h,x:x+w])
            ids.append(id)

    return faceSamples,ids

print ("Training faces. It will take a few seconds. Wait ...")

faces,ids = Images_And_Labels(path)
recognizer.train(faces, np.array(ids))

# Create trainer directory if it doesn't exist
trainer_dir = os.path.join(script_dir, 'trainer')
os.makedirs(trainer_dir, exist_ok=True)

trainer_file = os.path.join(trainer_dir, 'trainer.yml')
recognizer.write(trainer_file)  # Save the trained model as trainer.yml

print("✅ Model trained successfully! Now we can recognize your face.")