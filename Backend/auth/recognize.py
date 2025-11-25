import time
import cv2
import os


def AuthenticateFace():
    """
    Authenticate user via face recognition.
    Returns True if authenticated, False otherwise.
    """
    
    flag = False
    
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Check if trainer model exists
    trainer_file = os.path.join(script_dir, 'trainer', 'trainer.yml')
    if not os.path.exists(trainer_file):
        print("\n❌ Trainer model not found!")
        print("Please run the following steps first:")
        print("1. python Backend/auth/sample.py (to collect face samples)")
        print("2. python Backend/auth/trainer.py (to train the model)\n")
        return False
    
    # Local Binary Patterns Histograms
    recognizer = cv2.face.LBPHFaceRecognizer_create()

    recognizer.read(trainer_file)  # load trained model
    
    # Try to load cascade classifier
    cascadePath = os.path.join(script_dir, 'haarcascade_frontalface_default.xml')
    
    # Check if local file exists, if not use OpenCV's built-in
    if not os.path.exists(cascadePath):
        cascadePath = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    
    if not os.path.exists(cascadePath):
        print("\n❌ Error: Cascade file not found!")
        return False
    
    faceCascade = cv2.CascadeClassifier(cascadePath)
    
    if faceCascade.empty():
        print("\n❌ Error: Could not load cascade classifier!")
        return False

    font = cv2.FONT_HERSHEY_SIMPLEX  # denotes the font type

    id = 0  # default ID

    # Get user name from environment or use default
    user_name = os.getenv('USERNAME', 'User')
    names = ['Unknown', user_name]  # names, index 0 is unknown, index 1 is recognized user

    cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # cv2.CAP_DSHOW to remove warning
    cam.set(3, 640)  # set video FrameWidth
    cam.set(4, 480)  # set video FrameHeight
    cam.set(cv2.CAP_PROP_FPS, 30)  # Set frame rate to 30 FPS
    cam.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer to minimize lag

    # Define min window size to be recognized as a face
    minW = 0.1*cam.get(3)
    minH = 0.1*cam.get(4)

    print("\n👤 Face Authentication Started...")
    print("Look at the camera. Press ESC to cancel.\n")
    
    attempts = 0
    max_attempts = 100  # Maximum frames to check
    frame_skip = 0
    face_detected = False

    while attempts < max_attempts:
        attempts += 1
        
        ret, img = cam.read()  # read the frames using the above created object
        
        if not ret:
            continue
        
        frame_skip += 1
        
        # Process every 2nd frame for better performance
        if frame_skip % 2 != 0:
            cv2.imshow('Face Authentication', img)
            k = cv2.waitKey(1) & 0xff
            if k == 27:
                print("\n❌ Authentication cancelled by user.\n")
                break
            continue

        # The function converts an input image from one color space to another
        converted_image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        faces = faceCascade.detectMultiScale(
            converted_image,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(int(minW), int(minH)),
        )

        if len(faces) > 0 and not face_detected:
            face_detected = True
            print("✓ Face detected! Analyzing...")

        for(x, y, w, h) in faces:

            # used to draw a rectangle on any image
            cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2)

            # to predict on every single image
            id, confidence = recognizer.predict(converted_image[y:y+h, x:x+w])

            # Debug output
            print(f"Prediction - ID: {id}, Confidence: {confidence:.2f}")

            # Check if confidence is less than 100 (lower is better)
            if (confidence < 100):
                name = names[id] if id < len(names) else "Unknown"
                accuracy = "  {0}%".format(round(100 - confidence))
                
                # If confidence is good (less than 70), authenticate - more lenient threshold
                if confidence < 70:
                    flag = True
                    print(f"✓ Recognized with {100-confidence:.1f}% accuracy!")
                    cv2.putText(img, "Authenticated!", (x+5, y+h+30), font, 0.8, (0, 255, 0), 2)
            else:
                name = "Unknown"
                accuracy = "  {0}%".format(round(100 - confidence))

            cv2.putText(img, str(name), (x+5, y-5), font, 1, (255, 255, 255), 2)
            cv2.putText(img, str(accuracy), (x+5, y+h-5), font, 1, (255, 255, 0), 1)

        cv2.imshow('Face Authentication', img)

        k = cv2.waitKey(1) & 0xff  # Press 'ESC' for exiting video (reduced to 1ms)
        if k == 27:
            print("\n❌ Authentication cancelled by user.\n")
            break
        if flag:
            print(f"\n✅ Face authenticated successfully! Welcome {user_name}!\n")
            time.sleep(0.5)  # Show success message for 0.5 second
            break

    # Do a bit of cleanup
    cam.release()
    cv2.destroyAllWindows()
    
    if not flag:
        if not face_detected:
            print("\n❌ No face detected. Please ensure:")
            print("   - You are in a well-lit area")
            print("   - Camera is working properly")
            print("   - Your face is clearly visible\n")
        elif attempts >= max_attempts:
            print("\n⚠️  Face detected but not recognized.")
            print("   Try running trainer.py again to retrain the model.\n")
    
    return flag
