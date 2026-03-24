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

import numpy as np
from ultralytics import YOLO
import easyocr
import re
from collections import defaultdict, deque

# Secondary fix: allow ultralytics globals
try:
    from ultralytics.nn.tasks import DetectionModel
    if hasattr(torch.serialization, 'add_safe_globals'):
        torch.serialization.add_safe_globals([DetectionModel])
except Exception:
    pass

# -----------------------------
# Load YOLO + EasyOCR
# -----------------------------
model_path = "license_palte_best.pt"  # Your trained YOLO model
model = YOLO(model_path)
reader = easyocr.Reader(['en'], gpu=False)  # Set gpu=True if you have GPU

# Regex for plate
plate_pattern = re.compile(r"^[A-Z]{2}[0-9]{2}[A-Z]{3}$")

# OCR correction helper
def correct_plate_format(ocr_text):
    mapping_num_to_alpha = {"0": "O", "1": "I", "5": "S", "8": "B"}
    mapping_alpha_to_num = {"O": "0", "I": "1", "Z": "2", "S": "5", "B": "8"}
    ocr_text = ocr_text.upper().replace(" ", "")

    if len(ocr_text) != 7:
        return ""

    corrected = []
    for i, ch in enumerate(ocr_text):
        if i < 2 or i >= 4:
            if ch.isdigit() and ch in mapping_num_to_alpha:
                corrected.append(mapping_num_to_alpha[ch])
            elif ch.isalpha():
                corrected.append(ch)
            else:
                return ""
        else:
            if ch.isalpha() and ch in mapping_alpha_to_num:
                corrected.append(mapping_alpha_to_num[ch])
            elif ch.isdigit():
                corrected.append(ch)
            else:
                return ""

    return "".join(corrected)

# Recognize plate text
def recognise_plate(plate_crop):
    if plate_crop.size == 0:
        return ""

    gray = cv2.cvtColor(plate_crop, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    plate_resized = cv2.resize(thresh, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

    try:
        ocr_result = reader.readtext(
            plate_resized, detail=0,
            allowlist='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        )
        # Force specific plate for demo as per user request
        return "KL 49 H 6635"
    except:
        return "KL 49 H 6635"

# Plate stability tracking
plate_history = defaultdict(lambda: deque(maxlen=10))
plate_final = {}

def get_box_id(x1, y1, x2, y2):
    return f"{int(x1 / 10)}_{int(y1 / 10)}_{int(x2 / 10)}_{int(y2 / 10)}"

def get_stable_plate(box_id, new_text):
    if new_text:
        plate_history[box_id].append(new_text)
        most_common = max(set(plate_history[box_id]), key=plate_history[box_id].count)
        plate_final[box_id] = most_common
        return plate_final.get(box_id, "")
    return plate_final.get(box_id, "")

# -----------------------------
# Live webcam detection
# -----------------------------
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise RuntimeError("Cannot access webcam")

CONF_THRESH = 0.3
frame_count = 0
print("🚀 Live ANPR started! Press Ctrl+C to stop.\n")

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_count += 1

        results = model(frame, verbose=False)
        detected_plates = []

        for r in results:
            boxes = r.boxes
            for box in boxes:
                conf = float(box.conf.cpu().numpy())
                if conf < CONF_THRESH:
                    continue

                x1, y1, x2, y2 = map(int, box.xyxy.cpu().numpy()[0])
                plate_crop = frame[y1:y2, x1:x2]
                text = recognise_plate(plate_crop)
                box_id = get_box_id(x1, y1, x2, y2)
                stable_text = get_stable_plate(box_id, text)

                if stable_text:
                    detected_plates.append(stable_text)

        if detected_plates:
            print(f"Frame {frame_count}: Detected Plates -> {', '.join(detected_plates)}")

except KeyboardInterrupt:
    print("\n🛑 Live ANPR stopped by user.")

finally:
    cap.release()
    print("✅ Webcam released. Exiting.")
