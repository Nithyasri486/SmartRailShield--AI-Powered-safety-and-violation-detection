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
import time

# Secondary fix: allow ultralytics globals
try:
    from ultralytics.nn.tasks import DetectionModel
    if hasattr(torch.serialization, 'add_safe_globals'):
        torch.serialization.add_safe_globals([DetectionModel])
except Exception:
    pass

class ObstacleDetector:
    def __init__(self, model_path="best.pt", conf_threshold=0.5):
        print("🚀 Loading YOLO model for obstacle detection...")
        self.model = YOLO(model_path)
        self.conf_threshold = conf_threshold
        print("✅ YOLO model loaded successfully.")

        self.last_detected_time = 0
        self.detected_objects = []

    def detect_obstacles(self, frame):
        """
        Detect obstacles in a frame using YOLO.
        Returns list of detected objects.
        """
        results = self.model(frame, verbose=False)
        detections = []

        for r in results:
            boxes = r.boxes
            for box in boxes:
                conf = float(box.conf[0])
                if conf < self.conf_threshold:
                    continue

                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cls_id = int(box.cls[0])
                label = self.model.names[cls_id]

                detections.append({
                    "label": label,
                    "confidence": conf,
                    "bbox": (x1, y1, x2, y2)
                })

        self.detected_objects = detections
        self.last_detected_time = time.time()
        return detections

    def draw_detections(self, frame, detections):
        """
        Draw bounding boxes and labels on frame.
        """
        for det in detections:
            x1, y1, x2, y2 = det["bbox"]
            label = det["label"]
            conf = det["confidence"]

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
            cv2.putText(frame, f"{label} {conf:.2f}",
                        (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX,
                        0.6, (0, 0, 255), 2)

        return frame

    def run_live(self, source=0):
        """
        Run obstacle detection live using webcam.
        Press 'q' to quit.
        """
        cap = cv2.VideoCapture(source)

        if not cap.isOpened():
            print("❌ Unable to open video source")
            return

        print("🎥 Obstacle detection started. Press 'q' to quit.")

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            detections = self.detect_obstacles(frame)
            frame = self.draw_detections(frame, detections)

            cv2.imshow("🚧 SmartRail Shield - Obstacle Detection", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    detector = ObstacleDetector(model_path="best.pt", conf_threshold=0.5)
    detector.run_live(0)
