import cv2
import sys

print("Testing camera access...")
print("-" * 50)

# Try different camera indices
for camera_index in [0, 1, 2]:
    print(f"\nTrying camera index {camera_index}...")
    cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
    
    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            print(f"✅ Camera {camera_index} works!")
            print(f"   Resolution: {frame.shape[1]}x{frame.shape[0]}")
            cap.release()
        else:
            print(f"❌ Camera {camera_index} opened but can't read frames")
            cap.release()
    else:
        print(f"❌ Camera {camera_index} failed to open")

print("\n" + "-" * 50)
print("Camera test complete!")
print("\nIf a camera works above, use that index in the Streamlit app.")
