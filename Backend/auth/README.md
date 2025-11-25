# Face Authentication Setup

## 🔐 Overview
This face authentication system secures your Hey Dude voice assistant by requiring face recognition before the web UI loads.

## 📋 Prerequisites
Make sure you have installed:
```bash
pip install opencv-contrib-python
pip install pillow
pip install numpy
```

## 🚀 Setup Steps

### Step 1: Collect Face Samples
Run this command to capture 100 images of your face:
```bash
python Backend/auth/sample.py
```

**What happens:**
- Camera window opens
- Enter a numeric User ID (e.g., 1)
- Look at the camera from different angles
- 100 photos will be captured automatically
- Photos saved in `Backend/auth/samples/`
- Press ESC to stop early

**Tips for best results:**
- Good lighting
- Look straight, left, right, up, down
- Different facial expressions
- With/without glasses (if you wear them)

### Step 2: Train the Model
After collecting samples, train the recognition model:
```bash
python Backend/auth/trainer.py
```

**What happens:**
- Processes all images in `samples/` folder
- Trains LBPH face recognition model
- Saves trained model to `Backend/auth/trainer/trainer.yml`
- Takes a few seconds

### Step 3: Run the Application
Now start Hey Dude normally:
```bash
python run.py
```

**What happens:**
1. 🔐 Face authentication window opens
2. Look at the camera
3. ✅ If authenticated → Web UI loads
4. ❌ If failed → Application exits

## 🎯 Authentication Flow

```
python run.py
    ↓
Face Authentication
    ↓
├─ ✅ Success → Load Web UI → Voice Assistant Ready
└─ ❌ Failed  → Exit Application
```

## ⚙️ Configuration

### Skip Face Authentication (for testing)
Set environment variable:
```bash
# Windows PowerShell
$env:SKIP_FACE_AUTH="true"
python run.py

# Windows CMD
set SKIP_FACE_AUTH=true
python run.py
```

### Keyboard Shortcuts
- **ESC** - Cancel authentication

## 📁 File Structure
```
Backend/auth/
├── sample.py                           # Capture face samples
├── trainer.py                          # Train recognition model
├── recognize.py                        # Face authentication
├── haarcascade_frontalface_default.xml # Haar Cascade classifier
├── samples/                            # Captured face images
│   └── face.1.1.jpg, face.1.2.jpg...
└── trainer/
    └── trainer.yml                     # Trained model
```

## 🔧 Troubleshooting

### Camera not opening
- Check if another app is using the camera
- Try changing camera index in code (0 to 1)

### "Trainer model not found"
- Run `sample.py` and `trainer.py` first
- Check if `trainer.yml` exists

### Low accuracy / Not recognizing
- Collect more samples (run sample.py again with same ID)
- Ensure good lighting during training and authentication
- Keep face centered in frame

### Multiple users
- Run `sample.py` with different User IDs for each person
- Modify `recognize.py` names list to include all users

## 📊 Technical Details

**Algorithm:** LBPH (Local Binary Patterns Histograms)
- Fast and efficient
- Works well in varying lighting conditions
- Confidence score based (lower = better match)

**Confidence Threshold:** < 50
- Below 50 = Authenticated
- Above 50 = Unknown/Rejected

**Model:** OpenCV cv2.face.LBPHFaceRecognizer
- Trained on grayscale images
- Stored as YML file
- Lightweight and portable
