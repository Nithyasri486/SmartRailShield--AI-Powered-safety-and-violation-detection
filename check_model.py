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

# Secondary fix: allow ultralytics globals
try:
    from ultralytics.nn.tasks import DetectionModel
    if hasattr(torch.serialization, 'add_safe_globals'):
        torch.serialization.add_safe_globals([DetectionModel])
except Exception:
    pass

# Load the model
script_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(script_dir, "best.pt")

print(f"Loading model from: {model_path}")
print(f"Model exists: {os.path.exists(model_path)}")

model = YOLO(model_path)

print("\n" + "="*50)
print("YOLO Model Information:")
print("="*50)
print(f"\nModel classes: {model.names}")
print(f"Number of classes: {len(model.names)}")
print("\nDetectable objects:")
for idx, name in model.names.items():
    print(f"  {idx}: {name}")
