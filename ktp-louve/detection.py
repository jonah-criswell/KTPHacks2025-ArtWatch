import os
import cv2
import numpy as np
import pygame
import json
from ultralytics import YOLO
from openvino.runtime import Core
from datetime import datetime

# Initialize pygame mixer for audio
pygame.mixer.init()

OBJECT_NAME = "bottle"
ALERT_SOUND = "AGAIN_fetty.mp3"
MOVE_THRESHOLD = 50
MODEL_NAME = "yolov8n.pt"
STATUS_FILE = "status.json"  # Shared status file

def play_alert():
    try:
        pygame.mixer.music.load(ALERT_SOUND)
        pygame.mixer.music.play()
    except Exception as e:
        print(f"⚠️ Sound error: {e}")

def update_status_file(status):
    """Write status to JSON file for web server to read"""
    try:
        with open(STATUS_FILE, 'w') as f:
            json.dump(status, f)
    except Exception as e:
        print(f"⚠️ Status file error: {e}")

# Initialize status
status = {
    "object_present": False,
    "last_seen": None,
    "movement_detected": False,
    "last_movement": None,
    "status_message": "Initializing..."
}
update_status_file(status)

script_dir = os.path.dirname(os.path.abspath(__file__))
model_dir = os.path.join(script_dir, "yolov8n_openvino_model")
model_xml_path = os.path.join(model_dir, "yolov8n.xml")

print("🔧 Loading YOLOv8 model...")
model = YOLO(MODEL_NAME)

if not os.path.exists(model_xml_path):
    print("🧩 OpenVINO model not found — exporting...")
    export_path = model.export(format="openvino")
    model_dir = export_path
    model_xml_path = os.path.join(model_dir, "yolov8n.xml")
else:
    print(f"✅ Found existing OpenVINO model at:\n{model_xml_path}")

print("🚀 Loading OpenVINO model...")
ie = Core()
ov_model = ie.read_model(model=model_xml_path)
compiled_model = ie.compile_model(model=ov_model, device_name="CPU")

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise Exception("❌ Camera not found or cannot be opened!")

prev_position = None
frames_missing = 0
MISSING_THRESHOLD = 30  # Consider missing after 30 frames (~1 second)

def has_moved(prev, current, threshold=MOVE_THRESHOLD):
    if prev is None or current is None:
        return False
    return np.linalg.norm(np.array(prev) - np.array(current)) > threshold

print("✅ Ready — Detection running!")
print("🌐 Run 'python web_server.py' in another terminal to start the web interface")

frame_count = 0
while True:
    ret, frame = cap.read()
    if not ret:
        break

    input_image = cv2.resize(frame, (640, 640))
    input_rgb = cv2.cvtColor(input_image, cv2.COLOR_BGR2RGB)
    input_tensor = np.expand_dims(input_rgb.transpose(2, 0, 1), 0).astype(np.float32) / 255.0

    result = compiled_model([input_tensor])
    output = result[compiled_model.output(0)]

    if len(output.shape) == 3:
        output = output[0].T

    target_position = None
    boxes = []
    scores = []
    class_ids = []

    for det in output:
        x_center, y_center, width, height = det[:4]
        class_scores = det[4:]
        cls = np.argmax(class_scores)
        conf = class_scores[cls]
        
        if conf < 0.5:
            continue

        x1 = int((x_center - width / 2) * frame.shape[1] / 640)
        y1 = int((y_center - height / 2) * frame.shape[0] / 640)
        x2 = int((x_center + width / 2) * frame.shape[1] / 640)
        y2 = int((y_center + height / 2) * frame.shape[0] / 640)

        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(frame.shape[1], x2), min(frame.shape[0], y2)

        boxes.append([x1, y1, x2, y2])
        scores.append(float(conf))
        class_ids.append(cls)
    
    if len(boxes) > 0:
        indices = cv2.dnn.NMSBoxes(boxes, scores, score_threshold=0.5, nms_threshold=0.4)
        
        if len(indices) > 0:
            for i in indices.flatten():
                x1, y1, x2, y2 = boxes[i]
                conf = scores[i]
                cls = class_ids[i]
                class_name = model.names.get(cls, str(cls))

                color = (0, 255, 0) if class_name == OBJECT_NAME else (255, 0, 0)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, f"{class_name} {conf:.2f}", (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

                if class_name == OBJECT_NAME:
                    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                    target_position = (cx, cy)

    # Update status
    if target_position is not None:
        frames_missing = 0
        status["object_present"] = True
        status["last_seen"] = datetime.now().strftime("%I:%M:%S %p")
        status["status_message"] = "Object detected ✓"
        
        if has_moved(prev_position, target_position):
            print(f"🚨 Object moved!")
            play_alert()
            status["movement_detected"] = True
            status["last_movement"] = datetime.now().strftime("%I:%M:%S %p")
    else:
        frames_missing += 1
        if frames_missing > MISSING_THRESHOLD:
            status["object_present"] = False
            status["status_message"] = f"⚠️ Missing for {frames_missing} frames"
            if frames_missing == MISSING_THRESHOLD + 1:
                print("🚨 OBJECT STOLEN/MISSING!")
                play_alert()

    # Write status to file every frame
    update_status_file(status)

    prev_position = target_position
    frame_count += 1

    cv2.imshow("Object Movement Detector", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
pygame.mixer.quit()