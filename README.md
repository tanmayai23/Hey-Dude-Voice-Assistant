# 🎙️ Hey Dude - AI Voice Assistant

<div align="center">

![Hey Dude Logo](Frontend/assets(%20images%20)/IMAGES/hey-dude-logo.png)

**An intelligent voice-controlled desktop assistant powered by Google Gemini AI**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Face Recognition](https://img.shields.io/badge/Security-Face%20Authentication-red.svg)](Backend/auth/)

</div>

---

## 📋 Table of Contents

- [Features](#-features)
- [Demo](#-demo)
- [Tech Stack](#-tech-stack)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Voice Commands](#-voice-commands)
- [Project Structure](#-project-structure)
- [Security](#-security)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Features

### 🔐 **Security**
- **Face Authentication** - Secure login using facial recognition (LBPH algorithm)
- **Privacy First** - All data stored locally, no cloud storage

### 🎤 **Voice Control**
- **Hotword Detection** - Wake assistant with "Hey Dude"
- **Natural Language Processing** - Understands conversational commands
- **Speech Recognition** - Powered by Google Speech Recognition
- **Text-to-Speech** - Natural voice responses

### 🤖 **AI Integration**
- **Google Gemini AI** - Answer general knowledge questions
- **Smart Command Routing** - Automatically distinguishes between commands and queries
- **Context-Aware** - Checks local database before using AI

### 💬 **WhatsApp Automation**
- Send messages to contacts
- Make voice calls
- Make video calls
- Automated contact lookup from database

### 🖥️ **System Control**
- Open desktop applications
- Launch websites
- Play YouTube videos
- Custom command database (add your own commands)

### 🎨 **Modern UI**
- **Glass Morphism Design** - Beautiful, modern interface
- **SiriWave Animation** - Real-time voice visualization
- **Dark Theme** - Easy on the eyes
- **Chat History** - Track all your interactions
- **Settings Panel** - Manage profile, commands, and contacts

---

## 🎬 Demo

### Main Interface
- Circular orb interface with particle effects
- Real-time SiriWave animation during voice recognition
- Search bar for text commands
- Chat history sidebar

### Key Interactions
1. **Say "Hey Dude"** → Assistant activates
2. **Give command** → "Open WhatsApp and send message"
3. **Ask question** → "What is artificial intelligence?"
4. **Type in search bar** → Instant command execution

---

## 🛠️ Tech Stack

### Backend
- **Python 3.8+**
- **Eel** - Python-JavaScript bridge
- **OpenCV** - Face recognition (cv2.face.LBPHFaceRecognizer)
- **Speech Recognition** - Google Speech API
- **pyttsx3** - Text-to-speech
- **PyAutoGUI** - Desktop automation
- **Google Generative AI** - Gemini AI integration
- **SQLite3** - Local database

### Frontend
- **HTML5/CSS3/JavaScript**
- **Bootstrap 5.3** - UI framework
- **jQuery** - DOM manipulation
- **SiriWave** - Voice visualization
- **Bootstrap Icons** - Icon library
- **Textillate.js** - Text animations

---

## 📦 Prerequisites

Before installation, ensure you have:

- **Python 3.8 or higher**
- **Microphone** - For voice input
- **Webcam** - For face authentication (optional)
- **Internet Connection** - For speech recognition and Gemini AI
- **WhatsApp Desktop** - For WhatsApp automation (optional)
- **Google Gemini API Key** - [Get it here](https://makersuite.google.com/app/apikey)

---

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/Hey-Dude-Voice-Assistant.git
cd Hey-Dude-Voice-Assistant
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Additional Requirements

```bash
# For face recognition (if needed)
pip install opencv-contrib-python

# For speech recognition
pip install SpeechRecognition pyaudio

# If pyaudio installation fails on Windows:
pip install pipwin
pipwin install pyaudio
```

---

## ⚙️ Configuration

### 1. Set Up Environment Variables

```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your API key
GEMINI_API_KEY=your_actual_api_key_here
```

### 2. Set Up Face Authentication (Optional)

```bash
# Run face sample collection (looks at webcam)
python Backend/auth/sample.py

# Train the face recognition model
python Backend/auth/trainer.py
```

### 3. Set Up Database

```bash
# Initialize database with sample data
python Backend/database.py
```

### 4. Import Contacts (Optional)

Place your contacts in `contacts.csv` format:
```csv
name,mobile_no,address
John Doe,9876543210,New York
```

Then run:
```bash
python Backend/database.py
```

---

## 🎮 Usage

### Start the Assistant

```bash
python run.py
```

### First Launch
1. **Face Authentication** - Look at the camera (if enabled)
2. **Browser Opens** - Interface loads at `http://localhost:8006`
3. **Say "Hey Dude"** - Activate the voice assistant
4. **Give Commands** - Start controlling your computer!

### Alternative: Skip Face Authentication

```bash
# In .env file, set:
SKIP_FACE_AUTH=true
```

---

## 🗣️ Voice Commands

### WhatsApp Commands
```
"Open WhatsApp and send message"
"Send WhatsApp message to [name]"
"Make WhatsApp voice call to [name]"
"Make WhatsApp video call to [name]"
```

### System Commands
```
"Open Chrome"
"Open Notepad"
"Open Calculator"
"Open [app name]"
```

### Web Commands
```
"Open YouTube"
"Open Google"
"Open Instagram"
"Open [website name]"
```

### YouTube Commands
```
"Play [song name] on YouTube"
"Play [video] on YouTube"
```

### General Queries (Gemini AI)
```
"What is artificial intelligence?"
"Who is the president of USA?"
"How does gravity work?"
"Explain quantum physics"
```

### Settings Commands
```
Click the gear icon to:
- Edit your profile
- Add custom system commands
- Add custom web commands
- Manage contacts
```

---

## 📁 Project Structure

```
Hey-Dude-Voice-Assistant/
├── Backend/
│   ├── auth/                    # Face authentication
│   │   ├── samples/            # Face images (not uploaded)
│   │   ├── trainer/            # Trained model (not uploaded)
│   │   ├── haarcascade_frontalface_default.xml
│   │   ├── recognize.py        # Face recognition logic
│   │   ├── sample.py           # Collect face samples
│   │   └── trainer.py          # Train face model
│   ├── add_app.py              # Add applications to database
│   ├── command.py              # Command routing logic
│   ├── config.py               # Settings database operations
│   ├── database.py             # Database initialization
│   ├── features.py             # Core features (open, play, etc.)
│   ├── gemini_ai.py            # Google Gemini AI integration
│   ├── helper.py               # Utility functions
│   └── whatsapp.py             # WhatsApp automation
├── Frontend/
│   ├── assets( images )/
│   │   ├── Audio/              # Sound effects
│   │   ├── IMAGES/             # Images and logos
│   │   └── vendore/            # Third-party libraries
│   ├── controller.js           # Settings panel logic
│   ├── index.html              # Main UI
│   ├── main.js                 # Core JavaScript
│   ├── script.js               # Particle effects
│   └── style.css               # Styling
├── .env.example                # Environment template
├── .gitignore                  # Git ignore rules
├── hotword_detection.py        # "Hey Dude" wake word
├── main.py                     # Application startup
├── run.py                      # Entry point
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

---

## 🔒 Security

### Data Privacy
- ✅ **All data stored locally** - No cloud uploads
- ✅ **Face data never shared** - Stays on your computer
- ✅ **API keys in .env** - Never committed to Git
- ✅ **Database excluded** - .gitignore protects personal data

### What's NOT Uploaded to GitHub
- `.env` - Your API keys
- `HeyDude.db` - Your personal database
- `contacts.csv` - Your contact list
- `Backend/auth/samples/` - Your face images
- `Backend/auth/trainer/trainer.yml` - Your face model

### Security Best Practices
1. **Never share your `.env` file**
2. **Keep your database private**
3. **Don't commit personal data**
4. **Use face authentication** for added security

---

## 🐛 Troubleshooting

### Microphone Not Working
```bash
# Test microphone
python -c "import speech_recognition as sr; r = sr.Recognizer(); print('Mic test:', r.energy_threshold)"

# Adjust sensitivity in Backend/command.py:
r.energy_threshold = 4000  # Increase if too sensitive
```

### Face Authentication Failing
```bash
# Retrain face model with more samples
python Backend/auth/sample.py  # Collect 100+ images
python Backend/auth/trainer.py # Train again

# Or skip face auth temporarily
# In .env: SKIP_FACE_AUTH=true
```

### WhatsApp Not Opening
- Ensure WhatsApp Desktop is installed
- Check path in `Backend/whatsapp.py`
- Try `os.startfile('whatsapp://')` in Python

### Gemini AI Not Responding
- Verify API key in `.env` file
- Check internet connection
- Ensure `google-generativeai` is installed
- Model name: `gemini-2.5-flash` (update if needed)

### Port Already in Use
```bash
# Change port in main.py
eel.start('index.html', mode='edge-app', port=8007)  # Use different port
```

---

## 🤝 Contributing

Contributions are welcome! Here's how:

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Commit your changes**
   ```bash
   git commit -m "Add amazing feature"
   ```
4. **Push to branch**
   ```bash
   git push origin feature/amazing-feature
   ```
5. **Open a Pull Request**

### Contribution Guidelines
- Follow PEP 8 for Python code
- Add comments for complex logic
- Test thoroughly before submitting
- Update README if adding features

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Google Gemini AI** - For powerful AI capabilities
- **OpenCV** - For face recognition
- **Eel Framework** - For Python-JavaScript bridge
- **Bootstrap** - For beautiful UI components
- **SiriWave** - For voice visualization

---

## 📧 Contact

**Project Maintainer**: [Your Name]

**GitHub**: [Your GitHub Profile](https://github.com/YOUR_USERNAME)

**Project Link**: [Hey Dude Voice Assistant](https://github.com/YOUR_USERNAME/Hey-Dude-Voice-Assistant)

---

<div align="center">

**⭐ Star this repo if you find it helpful!**

Made with ❤️ by [Your Name]

</div>
