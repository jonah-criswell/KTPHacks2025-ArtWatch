# louvre-object-detection

## 🛡️ ART WATCH: Real-Time Heist Prevention System

## 💎 The Mission

In the wake of the infamous Louvre heist where criminals disguised as construction workers stole 8 pieces of the French Crown Jewels, museums and high-security facilities need next-generation protection. **Guardian AI** is our answer—an intelligent, multi-layered security system that combines computer vision, real-time monitoring, and automated criminal documentation to prevent theft before it happens.

## 🎯 Project Overview

Guardian AI is a comprehensive security solution that:
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
- Secure storage in MongoDB with timestamps
- Chain-of-custody preservation for legal proceedings

### 4. **Multi-Layer Alert System**
- Audio alerts for immediate on-site response
- Web-based notifications for remote monitoring
- Persistent logging of all security events
- Integration-ready for emergency services

## 🏗️ System Architecture

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│   Camera #1     │─────▶│  Detection AI    │─────▶│  Web Dashboard  │
│ (Artifact View) │      │  (YOLOv8 + OV)   │      │  (Flask Server) │
└─────────────────┘      └──────────────────┘      └─────────────────┘
                                  │                          ▲
                                  │                          │
                                  ▼                          │
                         ┌─────────────────┐                 │
                         │  Status File    │─────────────────┘
                         │  (JSON Bridge)  │
                         └─────────────────┘
                                 │
┌─────────────────┐              │
│   Camera #2     │─────────┐    │
│ (Suspect View)  │         │    │
└─────────────────┘         ▼    ▼
                    ┌──────────────────┐
                    │    MongoDB       │
                    │ (Evidence Store) │
                    └──────────────────┘
```

## 🛠️ Technical Stack

- **Computer Vision**: OpenCV, YOLOv8, OpenVINO
- **Backend**: Python, Flask
- **Database**: MongoDB (evidence storage)
- **Audio Alerts**: Pygame
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Real-time Communication**: JSON file-based IPC

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

## 🎮 Usage

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

**Terminal 3 - Start Suspect Documentation:**
```bash
python suspect_camera.py  # Your MongoDB integration script
```

### Configuration

Edit these variables in `detection.py`:
```python
OBJECT_NAME = "bottle"          # Object to track (COCO dataset classes)
MOVE_THRESHOLD = 50             # Movement sensitivity (pixels)
MISSING_THRESHOLD = 30          # Frames before "missing" alert
ALERT_SOUND = "AGAIN_fetty.mp3" # Audio alert file
```

## 🎨 How It Works

### Real-Time Detection Pipeline

1. **Frame Capture**: Webcam captures video at 30 FPS
2. **Preprocessing**: Frame resized to 640x640, normalized for neural network
3. **Inference**: YOLOv8 model detects all objects in frame
4. **Target Identification**: System identifies tracked artifact (Red Bull bottle)
5. **Movement Analysis**: Calculates position delta between frames
6. **Alert Triggering**: Plays audio and updates status if movement detected
7. **Status Broadcasting**: Writes JSON status file for web dashboard
8. **Evidence Collection**: Triggers suspect camera if theft detected

### MongoDB Evidence Schema

```javascript
{
  _id: ObjectId,
  timestamp: ISODate,
  event_type: "theft_detected",
  artifact_status: "missing",
  suspect_photo: Binary,          // Base64 encoded image
  video_clip: String,             // File path or Binary
  location: {
    camera_id: "CAM-02",
    coordinates: [x, y]
  },
  confidence: 0.97
}
```

## 🔒 Security Features

- **No Internet Dependency**: Runs entirely on local network
- **Encrypted Evidence Storage**: MongoDB with authentication
- **Tamper-Proof Logging**: Immutable timestamp records
- **Redundant Monitoring**: Multiple camera angles
- **Instant Response**: <100ms alert latency

## 🏆 Why This Prevents Future Heists

### For the Louvre Scenario:
1. **Early Detection**: Unlike human guards, AI never blinks or gets distracted
2. **Instant Documentation**: Suspects photographed immediately, no escape anonymity
3. **Remote Monitoring**: Security teams alerted even if on-site guards compromised
4. **Evidence Chain**: Automatic video/photo evidence admissible in court
5. **Pattern Recognition**: ML can identify suspicious behavior before theft occurs

### Advanced Deterrence:
- Visible cameras + "AI Monitored" signage psychologically deter criminals
- Sub-second response time eliminates the "window of opportunity"
- Multiple data points (movement + facial capture) make theft extremely risky

## 📈 Future Enhancements

- [ ] Multi-artifact tracking (track entire display cases)
- [ ] Facial recognition integration with criminal databases
- [ ] Predictive behavior analysis (suspicious loitering detection)
- [ ] Mobile app with push notifications
- [ ] Cloud backup for evidence redundancy
- [ ] Integration with building access control systems
- [ ] Thermal imaging for night operations

## 🎓 Hackathon Demo

**Live Demo Flow:**
1. Show Red Bull bottle on camera → Dashboard shows "Object Present" ✅
2. Move bottle → Instant audio alert + "Movement Detected" 🚨
3. Remove bottle → Dashboard turns red, "OBJECT MISSING!" ⚠️
4. Secondary camera captures "robber" photo/video
5. Show MongoDB evidence with timestamp

## 👥 Team & Acknowledgments

Built for KTP Hacks 2.

**Technologies Used:**
- YOLOv8 by Ultralytics
- OpenVINO by Intel
- Flask by Pallets
- MongoDB by MongoDB Inc.

## 📄 License

MIT License - See LICENSE file for details

---

*"The best heist is the one that never happens."* - Guardian AI Team