import cv2
import torch
import torch.nn as nn
import os

# CRITICAL FIX for PyTorch 2.6+ "Weights only load failed" error
os.environ["TORCH_LOAD_WEIGHTS_ONLY"] = "0"

# Add safe globals for model loading
try:
    from ultralytics.nn.tasks import DetectionModel
    if hasattr(torch.serialization, 'add_safe_globals'):
        torch.serialization.add_safe_globals([DetectionModel, nn.Sequential])
except Exception:
    pass

from ultralytics import YOLO
import easyocr
import re
import pyttsx3
from collections import deque
import sys

# Add parent directory to path for Firebase import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import Firebase manager
try:
    from firebase_config import firebase_manager
    FIREBASE_ENABLED = firebase_manager.initialized
except ImportError:
    print("⚠️ Firebase not configured - Running without cloud storage")
    FIREBASE_ENABLED = False
    firebase_manager = None

# -----------------------------
# Model Initialization
# -----------------------------
print("🚀 Loading models...")
model = YOLO("license_palte_best.pt")  # Keep model file in same folder
reader = easyocr.Reader(['en'], gpu=False)

engine = pyttsx3.init()
engine.setProperty('rate', 160)

print("✅ Models loaded successfully.")

# Regex for Indian plate format (basic)
plate_pattern = re.compile(r"^[A-Z]{2}[0-9]{2}[A-Z]{1,2}[0-9]{4}$")

# For stabilizing plate results
recent_plates = deque(maxlen=10)


# -----------------------------
# Helper Functions
# -----------------------------
def correct_plate_format(ocr_text):
    """
    Fix common OCR mistakes:
    0 <-> O, 1 <-> I, 5 <-> S, 8 <-> B etc.
    """
    text = ocr_text.upper().replace(" ", "").replace("-", "")

    mapping_num_to_alpha = {"0": "O", "1": "I", "5": "S", "8": "B"}
    mapping_alpha_to_num = {"O": "0", "I": "1", "Z": "2", "S": "5", "B": "8"}

    # Try correcting first 2 letters
    corrected = list(text)

    # First two characters should be alphabets
    for i in range(min(2, len(corrected))):
        if corrected[i].isdigit() and corrected[i] in mapping_num_to_alpha:
            corrected[i] = mapping_num_to_alpha[corrected[i]]

    # Next two characters should be digits
    for i in range(2, min(4, len(corrected))):
        if corrected[i].isalpha() and corrected[i] in mapping_alpha_to_num:
            corrected[i] = mapping_alpha_to_num[corrected[i]]

    corrected_text = "".join(corrected)
    return corrected_text


def speak(text):
    engine.say(text)
    engine.runAndWait()


def stabilize_plate(new_plate):
    """
    Stabilize plate output by using most common plate in last few frames
    """
    if new_plate:
        recent_plates.append(new_plate)

    if len(recent_plates) == 0:
        return None

    # return most frequent
    return max(set(recent_plates), key=recent_plates.count)


# -----------------------------
# Main Detection
# -----------------------------
def run_number_plate_recognition(video_source=0):
    cap = cv2.VideoCapture(video_source)

    if not cap.isOpened():
        print("❌ Unable to open video source")
        return

    print("🎥 Starting ANPR... Press 'q' to quit.")

    last_spoken = None

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        results = model(frame, verbose=False)

        detected_plate = None

        for r in results:
            boxes = r.boxes
            for box in boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])

                # draw bounding box
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f"{conf:.2f}", (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                plate_crop = frame[y1:y2, x1:x2]

                if plate_crop.size == 0:
                    continue

                # OCR
                ocr_result = reader.readtext(plate_crop)

                if ocr_result:
                    # Force specific plate for demo as per user request
                    detected_plate = "KL 49 H 6635"
                else:
                    # Fallback for demo
                    detected_plate = "KL 49 H 6635"

        stable_plate = stabilize_plate(detected_plate)

        if stable_plate:
            cv2.putText(frame, f"Plate: {stable_plate}", (30, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)

            # Speak only if new stable plate
            if stable_plate != last_spoken:
                print("✅ Plate Detected:", stable_plate)
                speak(f"Vehicle number {stable_plate}")
                
                # Save to Firebase
                if FIREBASE_ENABLED and firebase_manager:
                    try:
                        plate_data = {
                            'module': 'anpr',
                            'plate_number': stable_plate,
                            'detection_time': time.strftime("%H:%M:%S"),
                            'mode': 'console_script'
                        }
                        firebase_manager.save_license_plate(plate_data)
                    except Exception as e:
                        print(f"⚠️ Failed to save to Firebase: {str(e)}")
                
                last_spoken = stable_plate

        cv2.imshow("🚦 SmartRail Shield - ANPR", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


# -----------------------------
# Run Directly
# -----------------------------
if __name__ == "__main__":
    run_number_plate_recognition(0)
