# 🛡️ ART WATCH: Real-Time Heist Prevention System

## 💎 The Mission

In the wake of the infamous Louvre heist where criminals disguised as construction workers stole 8 pieces of the French Crown Jewels, museums and high-security facilities need next-generation protection. **Art Watch** is our answer: an intelligent, multi-layered security system that combines computer vision, real-time monitoring, and automated criminal documentation to prevent theft before it happens.

## 🎯 Project Overview

ArtWatch is a comprehensive security solution built in a 12-hour private hackathon between members of Kappa Theta Pi - Phi Chapter, UGA first and only professional technology fraternity:
- **Tracks high-value artifacts** in real-time using AI-powered object detection
- **Detects unauthorized movement** instantly with sub-second response time
- **Documents suspects** automatically with facial capture and video evidence
- **Provides live monitoring** through an intuitive web dashboard
- **Stores criminal evidence** in a secure database for law enforcement

## 🚀 Key Features

### 1. **AI-Powered Artifact Tracking**
- YOLOv8 neural network optimized with OpenVINO for CPU efficiency
- Real-time object detection at 30+ FPS
- Precise movement tracking with configurable sensitivity
- Instant alerts when artifacts are moved or go missing

### 2. **Live Web Dashboard**
- Beautiful, responsive interface accessible from any device
- Real-time status updates (500ms refresh rate)
- Visual alerts with color-coded status indicators
- Connection monitoring to ensure system integrity
- Historical timeline of object movements

### 3. **Automated Suspect Documentation**
- Secondary camera system for robber identification
- Automatic photo capture when theft is detected
- Video clip recording for evidence

### 4. **Multi-Layer Alert System**
- Audio alerts for immediate on-site response
- Web-based notifications for remote monitoring
- Persistent logging of all security events
- Integration-ready for emergency services

## 🛠️ Tech Stack

- **Computer Vision**: OpenCV, YOLOv8,
- **Frontend**: React, Next.js, deployed with Vercel
- **Backend**: Python, Flask, Cloudflare tunnel to run python scripts locally and pass JSON to the deployed frontend
- **Audio Alerts**: Pygame

## 📦 Installation

### Prerequisites
```bash
# Python 3.8+
python --version

# MongoDB running locally or accessible instance
mongod --version
```

### Setup
```bash
# Clone the repository
git clone <your-repo-url>
cd guardian-ai

# Install dependencies
pip install opencv-python numpy pygame ultralytics openvino flask pymongo

# Add your alert sound
# Place "AGAIN_fetty.mp3" in the project directory

# Test camera access
python -c "import cv2; cap = cv2.VideoCapture(0); print('Camera OK' if cap.isOpened() else 'Camera Error')"
```

### Starting the System

**Terminal 1 - Start Detection Engine:**
```bash
python detection.py
```
This launches the AI detection system that monitors the artifact and triggers alerts.

**Terminal 2 - Start Web Dashboard:**
```bash
python web_server.py
```
Access the dashboard at: `http://localhost:5000`

**Terminal 3 - Start Suspect Documentation: (Optional)**
```bash
python suspect_camera.py  
```

### Configuration

Edit these variables in `detection.py`:
```python
OBJECT_NAME = "bottle"          # Object to track (COCO dataset classes)
MOVE_THRESHOLD = 50             # Movement sensitivity (pixels)
MISSING_THRESHOLD = 30          # Frames before "missing" alert
ALERT_SOUND = "AGAIN_fetty.mp3" # Audio alert file
```

## 👥 Team & Acknowledgments
Thank you to Kappa Theta Pi - Phi Chapter at the University of Georgia for organizing this private hackathon!
Shoutout to @arnavisharsh and @kanishkpaidimarry for being execellent teammates during this hackathon!
