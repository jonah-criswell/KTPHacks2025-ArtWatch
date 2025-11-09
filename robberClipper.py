import cv2
import time
import numpy as np
import sounddevice as sd
from collections import deque
import os

# --- SETTINGS ---
SOUND_THRESHOLD = 0.05   # Adjust this for sensitivity
DURATION_AFTER_SOUND = 5 # total clip length (2s before + 3s after)
SAMPLE_RATE = 44100      # audio sample rate

# --- OUTPUT FOLDER ---
os.makedirs("recordings", exist_ok=True)

# --- CAMERA SETUP ---
cap = cv2.VideoCapture(0)
frame_rate = int(cap.get(cv2.CAP_PROP_FPS)) or 30
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
buffer = deque(maxlen=frame_rate * 2)  # store last 2 seconds of frames

# --- SOUND DETECTION FUNCTION ---
def sound_callback(indata, frames, time_info, status):
    volume_norm = np.linalg.norm(indata) * 10
    global sound_detected
    if volume_norm > SOUND_THRESHOLD * 100:
        sound_detected = True
    return None

# --- START AUDIO STREAM ---
sound_detected = False
stream = sd.InputStream(callback=sound_callback, channels=1, samplerate=SAMPLE_RATE)
stream.start()

print("Listening for sounds... Press 'q' to quit.")

# --- MAIN LOOP ---
while True:
    ret, frame = cap.read()
    if not ret:
        break

    buffer.append(frame)

    if sound_detected:
        print("Sound detected! Recording 5-second clip...")
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        filename = os.path.join("recordings", f"sound_clip_{int(time.time())}.mp4")
        out = cv2.VideoWriter(filename, fourcc, frame_rate, (frame_width, frame_height))

        # Display recording status
        start_time_display = time.time()
        while time.time() - start_time_display < 1:
            display_frame = frame.copy()
            cv2.putText(display_frame, "🔴 Recording...", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
            cv2.imshow("Camera", display_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        # Save the last 2 seconds (from buffer)
        for f in list(buffer):
            out.write(f)

        # Then record 3 more seconds live
        start_time = time.time()
        while time.time() - start_time < DURATION_AFTER_SOUND - 2:
            ret, frame = cap.read()
            if not ret:
                break
            out.write(frame)
            display_frame = frame.copy()
            cv2.putText(display_frame, "🔴 Recording...", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
            cv2.imshow("Camera", display_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        out.release()
        print(f"Saved clip: {filename}")
        sound_detected = False

    # Exit key
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# --- CLEANUP ---
cap.release()
cv2.destroyAllWindows()
stream.stop()
stream.close()
