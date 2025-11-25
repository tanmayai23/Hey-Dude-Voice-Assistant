import cv2
import os

# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

cam = cv2.VideoCapture(0, cv2.CAP_DSHOW) #create a video capture object which is helpful to capture videos through webcam
cam.set(3, 640) # set video FrameWidth
cam.set(4, 480) # set video FrameHeight
cam.set(cv2.CAP_PROP_FPS, 30) # Set frame rate to 30 FPS
cam.set(cv2.CAP_PROP_BUFFERSIZE, 1) # Reduce buffer to minimize lag


# Try multiple methods to load the cascade classifier
cascade_path = os.path.join(script_dir, 'haarcascade_frontalface_default.xml')

# Check if local file exists, if not use OpenCV's built-in
if not os.path.exists(cascade_path):
    print("⚠️  Local cascade file not found, using OpenCV built-in...")
    cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'

# Verify the path exists before loading
if not os.path.exists(cascade_path):
    print("❌ Error: Cascade file not found!")
    print(f"Tried: {cascade_path}")
    input("Press Enter to exit...")
    exit(1)

print(f"Loading cascade from: {cascade_path}")
detector = cv2.CascadeClassifier(cascade_path)

# Verify it loaded correctly
if detector.empty():
    print("❌ Error: Could not load cascade classifier!")
    input("Press Enter to exit...")
    exit(1)

print(f"✅ Cascade classifier loaded successfully!")

face_id = input("Enter a Numeric user ID here: ")
#Use integer ID for every new face (0,1,2,3,4,5,6,7,8,9........)

print("Taking samples, look at camera ....... ")
count = 0 # Initializing sampling face count
frame_skip = 0 # Skip frames for faster capture

# Create samples directory if it doesn't exist (relative to script location)
samples_dir = os.path.join(script_dir, 'samples')
os.makedirs(samples_dir, exist_ok=True)

while True:

    ret, img = cam.read() #read the frames using the above created object
    
    if not ret:
        continue
    
    frame_skip += 1
    
    # Process every 2nd frame for faster performance
    if frame_skip % 2 != 0:
        cv2.imshow('image', img)
        k = cv2.waitKey(1) & 0xff
        if k == 27:
            break
        continue
    
    converted_image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) #The function converts an input image from one color space to another
    faces = detector.detectMultiScale(converted_image, scaleFactor=1.2, minNeighbors=5, minSize=(30, 30))

    for (x,y,w,h) in faces:

        cv2.rectangle(img, (x,y), (x+w,y+h), (0,255,0), 2) #used to draw a rectangle on any image
        count += 1

        # Save image to samples directory
        image_path = os.path.join(samples_dir, f"face.{face_id}.{count}.jpg")
        cv2.imwrite(image_path, converted_image[y:y+h,x:x+w], [cv2.IMWRITE_JPEG_QUALITY, 85])
        # To capture & Save images into the datasets folder
        
        # Display count on screen
        cv2.putText(img, f"Captured: {count}/100", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        cv2.imshow('image', img) #Used to display an image in a window

    k = cv2.waitKey(1) & 0xff # Waits for a pressed key (reduced to 1ms for faster response)
    if k == 27: # Press 'ESC' to stop
        break
    elif count >= 100: # Take 100 samples (More sample --> More accuracy)
         break

print("✅ Samples taken successfully! Now closing the program....")
cam.release()
cv2.destroyAllWindows()