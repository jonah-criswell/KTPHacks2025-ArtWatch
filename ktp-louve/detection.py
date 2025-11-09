import os
import cv2
import numpy as np
import pygame
import json
import time
from ultralytics import YOLO
from openvino.runtime import Core
from datetime import datetime

# Initialize pygame mixer for audio
pygame.mixer.init()

OBJECT_NAME = "bottle"
ALERT_SOUND = "AGAIN_fetty.mp3"
MOVE_THRESHOLD = 100
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
    "status_message": "Initializing...",
    "bottles": [],  # Array of individual bottle statuses
    "total_bottles": 0,
    "present_count": 0,
    "missing_count": 0,
    "max_bottles_seen": 0
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

# Track multiple bottles: {id: {'position': (x, y), 'frames_seen': count, 'last_seen_time': timestamp, 'missing_alerted': bool, 'initial_position': (x, y)}}
tracked_bottles = {}
max_bottles_seen_simultaneously = 0  # Track the maximum number of bottles seen at once
MISSING_TIME_THRESHOLD = 2.0  # Alert if bottle missing for more than 2 seconds
MATCH_DISTANCE_THRESHOLD = 100  # Max distance to match a bottle between frames

def has_moved(prev, current, threshold=MOVE_THRESHOLD):
    if prev is None or current is None:
        return False
    return np.linalg.norm(np.array(prev) - np.array(current)) > threshold

def match_bottles(prev_bottles, current_positions, match_threshold=MATCH_DISTANCE_THRESHOLD, current_time=None):
    """Match current bottle positions to previous tracked bottles"""
    matched = {}
    used_current = set()
    
    if current_time is None:
        current_time = time.time()
    
    # Extract just positions for matching (first 2 elements)
    current_pos_only = [(pos[0], pos[1]) for pos in current_positions]
    
    # First, try to match active bottles (those that were seen recently)
    for bottle_id, bottle_data in prev_bottles.items():
        # Skip bottles that have been missing for a long time and already alerted
        # We'll try to reuse their IDs later if needed
        last_seen = bottle_data.get('last_seen_time', current_time)
        time_missing = current_time - last_seen
        if time_missing > MISSING_TIME_THRESHOLD and bottle_data.get('missing_alerted', False):
            # Skip already-alerted missing bottles for matching
            continue
            
        prev_pos = bottle_data.get('position')
        if prev_pos is None:
            continue
            
        best_match = None
        best_distance = match_threshold
        
        for i, curr_pos in enumerate(current_pos_only):
            if i in used_current:
                continue
            distance = np.linalg.norm(np.array(prev_pos) - np.array(curr_pos))
            if distance < best_distance:
                best_distance = distance
                best_match = i
        
        if best_match is not None:
            matched[bottle_id] = current_positions[best_match]  # Store full position data
            used_current.add(best_match)
        else:
            # Bottle not found in current frame
            matched[bottle_id] = None
    
    # Add new bottles for unmatched current positions
    return matched, used_current

def get_available_bottle_id(tracked_bottles, max_allowed, current_time=None):
    """Get an available bottle ID within the range [0, max_allowed-1], reusing missing bottle IDs first"""
    if max_allowed <= 0:
        return 0
    
    if current_time is None:
        current_time = time.time()
    
    # First, try to find an unused ID slot (0 to max_allowed-1)
    for bottle_id in range(max_allowed):
        if bottle_id not in tracked_bottles:
            return bottle_id
    
    # All IDs in range are taken, try to find a missing bottle ID to reuse
    # (bottles that have been missing for longer than threshold)
    for bottle_id in range(max_allowed):
        if bottle_id in tracked_bottles:
            bottle_data = tracked_bottles[bottle_id]
            last_seen = bottle_data.get('last_seen_time', current_time)
            time_missing = current_time - last_seen
            if time_missing > MISSING_TIME_THRESHOLD:
                # This ID is available for reuse (bottle has been missing)
                return bottle_id
    
    # All IDs are active, find the one that's been missing the longest to reuse
    oldest_missing_id = None
    longest_missing_time = 0
    for bottle_id in range(max_allowed):
        if bottle_id in tracked_bottles:
            bottle_data = tracked_bottles[bottle_id]
            last_seen = bottle_data.get('last_seen_time', current_time)
            time_missing = current_time - last_seen
            if time_missing > longest_missing_time:
                longest_missing_time = time_missing
                oldest_missing_id = bottle_id
    
    if oldest_missing_id is not None:
        return oldest_missing_id
    
    # Fallback: return first available ID (shouldn't reach here if logic is correct)
    return 0

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

    current_bottle_positions = []  # Initialize list for current frame's bottle positions
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

                # Draw detection boxes for non-bottle objects only
                # Bottles will be drawn with IDs in the tracking section
                if class_name != OBJECT_NAME:
                    color = (255, 0, 0)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(frame, f"{class_name} {conf:.2f}", (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                else:
                    # Store bottle position and bbox for tracking
                    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                    current_bottle_positions.append((cx, cy, x1, y1, x2, y2))

    # Track multiple bottles
    current_bottles = {}
    alert_triggered = False
    current_time = time.time()  # Get current timestamp for this frame
    
    # Update maximum bottles seen simultaneously
    num_bottles_current = len(current_bottle_positions)
    if num_bottles_current > max_bottles_seen_simultaneously:
        max_bottles_seen_simultaneously = num_bottles_current
        print(f"📊 Maximum bottles seen simultaneously updated to: {max_bottles_seen_simultaneously}")
    
    if len(current_bottle_positions) > 0:
        # Match current positions to tracked bottles (including trying to match to missing bottles)
        matched_bottles, used_positions = match_bottles(tracked_bottles, current_bottle_positions, current_time=current_time)
        
        # Also try to match unmatched positions to missing bottles (for ID reuse)
        unmatched_positions = [(i, pos) for i, pos in enumerate(current_bottle_positions) if i not in used_positions]
        # Find missing bottles that haven't been alerted yet (so we can try to match them)
        missing_bottle_ids = []
        for bid, bdata in tracked_bottles.items():
            if bid < max_bottles_seen_simultaneously:
                last_seen = bdata.get('last_seen_time', current_time)
                time_missing = current_time - last_seen
                if time_missing > MISSING_TIME_THRESHOLD and not bdata.get('missing_alerted', False):
                    missing_bottle_ids.append(bid)
        
        # Try to match unmatched positions to missing bottle IDs
        for missing_id in missing_bottle_ids:
            if not unmatched_positions:
                break
            if 'position' not in tracked_bottles[missing_id]:
                continue
            missing_pos = tracked_bottles[missing_id]['position']
            best_match_idx = None
            best_match_pos_idx = None
            best_distance = MATCH_DISTANCE_THRESHOLD
            
            for pos_idx, (curr_idx, pos_data) in enumerate(unmatched_positions):
                curr_pos = (pos_data[0], pos_data[1])
                distance = np.linalg.norm(np.array(missing_pos) - np.array(curr_pos))
                if distance < best_distance:
                    best_distance = distance
                    best_match_idx = curr_idx
                    best_match_pos_idx = pos_idx
            
            if best_match_idx is not None:
                # Reuse this missing bottle's ID
                matched_bottles[missing_id] = current_bottle_positions[best_match_idx]
                used_positions.add(best_match_idx)
                unmatched_positions.pop(best_match_pos_idx)
        
        # Update matched bottles
        for bottle_id, new_position_data in matched_bottles.items():
            if new_position_data is not None:
                # Extract position from tuple (cx, cy, x1, y1, x2, y2)
                new_position = (new_position_data[0], new_position_data[1])
                
                # Check if this bottle was previously missing (reused ID)
                last_seen = tracked_bottles[bottle_id].get('last_seen_time', current_time)
                time_missing = current_time - last_seen
                was_missing = time_missing > MISSING_TIME_THRESHOLD
                
                # Bottle found - update last seen time and reset missing alert flag
                tracked_bottles[bottle_id]['last_seen_time'] = current_time
                tracked_bottles[bottle_id]['missing_alerted'] = False  # Reset alert flag since bottle is back
                
                # Bottle found - check for movement
                prev_pos = tracked_bottles[bottle_id].get('position', new_position)
                initial_pos = tracked_bottles[bottle_id].get('initial_position', prev_pos)
                
                # If bottle was missing and is now found, reset it as a new detection
                if was_missing:
                    # Reset the bottle as if it's new (new initial position, reset movement alert)
                    tracked_bottles[bottle_id] = {
                        'position': new_position,
                        'initial_position': new_position,
                        'frames_seen': 1,
                        'last_seen_time': current_time,
                        'missing_alerted': False,
                        'movement_alerted': False,
                        'bbox': (new_position_data[2], new_position_data[3], 
                                new_position_data[4], new_position_data[5]),
                        'settling_frames': 10
                    }
                    current_bottles[bottle_id] = tracked_bottles[bottle_id]
                    continue
                
                # Update settling frames counter
                settling_frames = tracked_bottles[bottle_id].get('settling_frames', 0)
                is_settled = (settling_frames == 0)
                
                if settling_frames > 0:
                    tracked_bottles[bottle_id]['settling_frames'] = settling_frames - 1
                    # After settling completes, lock in the initial position
                    if tracked_bottles[bottle_id]['settling_frames'] == 0:
                        tracked_bottles[bottle_id]['initial_position'] = new_position
                        is_settled = True
                
                # Check if moved significantly from initial position or previous position
                # Only check movement after settling period
                if is_settled:
                    # Use the locked initial position for comparison
                    locked_initial = tracked_bottles[bottle_id].get('initial_position', new_position)
                    moved_from_initial = has_moved(locked_initial, new_position, threshold=MOVE_THRESHOLD * 2)
                    moved_from_prev = has_moved(prev_pos, new_position)
                    
                    if moved_from_initial or moved_from_prev:
                        if not tracked_bottles[bottle_id].get('movement_alerted', False):
                            print(f"🚨 Bottle {bottle_id} moved!")
                            play_alert()
                            alert_triggered = True
                            status["movement_detected"] = True
                            status["last_movement"] = datetime.now().strftime("%I:%M:%S %p")
                            tracked_bottles[bottle_id]['movement_alerted'] = True
                
                tracked_bottles[bottle_id]['position'] = new_position
                tracked_bottles[bottle_id]['frames_seen'] = tracked_bottles[bottle_id].get('frames_seen', 0) + 1
                if 'settling_frames' not in tracked_bottles[bottle_id]:
                    tracked_bottles[bottle_id]['settling_frames'] = 10
                if 'initial_position' not in tracked_bottles[bottle_id]:
                    tracked_bottles[bottle_id]['initial_position'] = new_position
                
                # Store bbox for display
                tracked_bottles[bottle_id]['bbox'] = (new_position_data[2], new_position_data[3], 
                                                     new_position_data[4], new_position_data[5])
                current_bottles[bottle_id] = tracked_bottles[bottle_id]
            else:
                # Bottle not found in current frame - check if it's been missing long enough to alert
                last_seen = tracked_bottles[bottle_id].get('last_seen_time', current_time)
                time_missing = current_time - last_seen
                
                # Check if bottle has been missing for more than threshold and we haven't alerted yet
                if time_missing > MISSING_TIME_THRESHOLD and not tracked_bottles[bottle_id].get('missing_alerted', False):
                    print(f"🚨 Bottle {bottle_id} STOLEN/MISSING! (missing for {time_missing:.2f}s)")
                    play_alert()
                    alert_triggered = True
                    tracked_bottles[bottle_id]['missing_alerted'] = True  # Mark as alerted to prevent repeated alerts
                    
                # Keep tracking the bottle even if missing (for potential recovery)
                if 'position' in tracked_bottles[bottle_id]:
                    current_bottles[bottle_id] = tracked_bottles[bottle_id]
        
        # Add new bottles for unmatched positions
        # The max_bottles_seen_simultaneously was already updated at the start based on current detections
        unmatched_indices = [i for i in range(len(current_bottle_positions)) if i not in used_positions]
        
        # Create new bottles for unmatched positions
        for i in unmatched_indices:
            pos_data = current_bottle_positions[i]
            # Get an available ID within the max range (0 to max_bottles_seen_simultaneously-1)
            bottle_id = get_available_bottle_id(tracked_bottles, max_bottles_seen_simultaneously, current_time=current_time)
            
            pos = (pos_data[0], pos_data[1])
            tracked_bottles[bottle_id] = {
                'position': pos,
                'initial_position': pos,
                'frames_seen': 1,
                'last_seen_time': current_time,
                'missing_alerted': False,
                'movement_alerted': False,
                'bbox': (pos_data[2], pos_data[3], pos_data[4], pos_data[5]),
                'settling_frames': 10  # Wait 10 frames before alerting on movement
            }
            current_bottles[bottle_id] = tracked_bottles[bottle_id]
    else:
        # No bottles detected in current frame - check all tracked bottles for missing time
        for bottle_id in tracked_bottles.keys():
            last_seen = tracked_bottles[bottle_id].get('last_seen_time', current_time)
            time_missing = current_time - last_seen
            
            # Check if bottle has been missing for more than threshold and we haven't alerted yet
            if time_missing > MISSING_TIME_THRESHOLD and not tracked_bottles[bottle_id].get('missing_alerted', False):
                print(f"🚨 Bottle {bottle_id} STOLEN/MISSING! (missing for {time_missing:.2f}s)")
                play_alert()
                alert_triggered = True
                tracked_bottles[bottle_id]['missing_alerted'] = True  # Mark as alerted to prevent repeated alerts
                
            # Keep tracking the bottle even if missing (for potential recovery)
            if 'position' in tracked_bottles[bottle_id]:
                current_bottles[bottle_id] = tracked_bottles[bottle_id]
    
    # Check for missing bottles and update status with individual bottle information
    any_missing = False
    bottles_count = 0
    missing_count = 0
    bottles_status_list = []
    last_movement_time = None
    last_seen_time = None
    any_movement_detected = False
    
    # Build individual bottle statuses
    for bottle_id in range(max_bottles_seen_simultaneously):
        if bottle_id in tracked_bottles:
            bottle_data = tracked_bottles[bottle_id]
            last_seen = bottle_data.get('last_seen_time', current_time)
            time_missing = current_time - last_seen
            is_missing = time_missing > MISSING_TIME_THRESHOLD
            
            bottle_status = {
                "id": bottle_id,
                "present": not is_missing,
                "last_seen": datetime.fromtimestamp(last_seen).strftime("%I:%M:%S %p") if last_seen else None,
                "missing_for": round(time_missing, 2) if is_missing else 0,
                "movement_detected": bottle_data.get('movement_alerted', False),
                "missing_alerted": bottle_data.get('missing_alerted', False)
            }
            
            # Add position if available
            if 'position' in bottle_data:
                bottle_status["position"] = {
                    "x": int(bottle_data['position'][0]),
                    "y": int(bottle_data['position'][1])
                }
            
            bottles_status_list.append(bottle_status)
            
            if is_missing:
                any_missing = True
                missing_count += 1
            else:
                bottles_count += 1
                if last_seen_time is None or last_seen > last_seen_time:
                    last_seen_time = last_seen
            
            if bottle_data.get('movement_alerted', False):
                any_movement_detected = True
                # Track the most recent movement
                if last_movement_time is None or last_seen > last_movement_time:
                    last_movement_time = last_seen
    
    # Update overall status
    status["bottles"] = bottles_status_list
    status["total_bottles"] = max_bottles_seen_simultaneously
    status["present_count"] = bottles_count
    status["missing_count"] = missing_count
    status["max_bottles_seen"] = max_bottles_seen_simultaneously
    
    if any_missing:
        status["object_present"] = False
        status["status_message"] = f"⚠️ {missing_count} bottle(s) missing!"
    elif bottles_count > 0:
        status["object_present"] = True
        status["last_seen"] = datetime.fromtimestamp(last_seen_time).strftime("%I:%M:%S %p") if last_seen_time else None
        status["status_message"] = f"{bottles_count} bottle(s) detected ✓"
    else:
        # No bottles detected at all
        if len(tracked_bottles) > 0:
            # We had bottles before but now none detected
            status["object_present"] = False
            status["status_message"] = "⚠️ All bottles missing!"
        else:
            # Initial state - no bottles tracked yet
            status["object_present"] = False
            status["status_message"] = "No bottles detected yet"
    
    # Update movement status
    status["movement_detected"] = any_movement_detected
    if last_movement_time:
        status["last_movement"] = datetime.fromtimestamp(last_movement_time).strftime("%I:%M:%S %p")
    else:
        status["last_movement"] = None
    
    # Display bottle IDs and bounding boxes on frame
    for bottle_id, bottle_data in current_bottles.items():
        last_seen = bottle_data.get('last_seen_time', current_time)
        time_missing = current_time - last_seen
        
        if 'bbox' in bottle_data and time_missing <= MISSING_TIME_THRESHOLD:
            x1, y1, x2, y2 = bottle_data['bbox']
            # Determine color based on movement status
            if bottle_data.get('movement_alerted', False):
                color = (0, 0, 255)  # Red for moved bottles
                label = f"Bottle #{bottle_id} MOVED!"
            else:
                color = (0, 255, 0)  # Green for stable bottles
                label = f"Bottle #{bottle_id}"
            
            # Draw bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)
            # Draw label with background for better visibility
            (text_width, text_height), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(frame, (x1, y2 + 5), (x1 + text_width + 10, y2 + text_height + 25), (0, 0, 0), -1)
            cv2.putText(frame, label, (x1 + 5, y2 + text_height + 15),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        elif time_missing > MISSING_TIME_THRESHOLD and 'position' in bottle_data:
            # Bottle missing - show last known position
            cx, cy = bottle_data['position']
            if not bottle_data.get('missing_alerted', False):
                # Still within threshold or just crossed it
                cv2.circle(frame, (int(cx), int(cy)), 25, (0, 165, 255), 3)  # Orange for missing
                cv2.putText(frame, f"Bottle #{bottle_id}?", (int(cx) - 50, int(cy) - 35),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 165, 255), 2)
            else:
                # Already alerted - show as missing
                cv2.circle(frame, (int(cx), int(cy)), 30, (0, 0, 255), 3)  # Red for confirmed missing
                cv2.putText(frame, f"Bottle #{bottle_id} MISSING!", (int(cx) - 70, int(cy) - 40),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    
    # Clean up bottles with IDs beyond the maximum allowed (max_bottles_seen_simultaneously)
    # Only keep bottles with IDs in range [0, max_bottles_seen_simultaneously-1]
    if max_bottles_seen_simultaneously > 0:
        bottles_to_remove = []
        for bid in tracked_bottles.keys():
            if bid >= max_bottles_seen_simultaneously:
                bottles_to_remove.append(bid)
        for bid in bottles_to_remove:
            del tracked_bottles[bid]
    
    # Display count on frame
    present_count = len([b for bid, b in tracked_bottles.items() 
                        if (current_time - b.get('last_seen_time', current_time)) <= MISSING_TIME_THRESHOLD])
    missing_count = len([b for bid, b in tracked_bottles.items() 
                        if (current_time - b.get('last_seen_time', current_time)) > MISSING_TIME_THRESHOLD])
    max_display = max_bottles_seen_simultaneously if max_bottles_seen_simultaneously > 0 else "?"
    cv2.putText(frame, f"Tracking: {present_count} present, {missing_count} missing (Max: {max_display})", (10, 30),
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    # Write status to file every frame
    update_status_file(status)
    frame_count += 1

    cv2.imshow("Object Movement Detector", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
pygame.mixer.quit()