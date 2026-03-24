"""
Camera Release Utility
This script releases all camera resources that might be held by other applications
"""

import cv2
import time
import sys

def release_all_cameras(max_cameras=3):
    """Release all camera resources"""
    print("🔄 Releasing all camera resources...")
    
    released = []
    for i in range(max_cameras):
        try:
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
            if cap.isOpened():
                cap.release()
                released.append(i)
                print(f"✅ Released camera {i}")
            else:
                print(f"ℹ️  Camera {i} not in use")
        except Exception as e:
            print(f"⚠️  Error with camera {i}: {str(e)}")
    
    # Destroy all OpenCV windows
    cv2.destroyAllWindows()
    
    # Wait a bit for cleanup
    time.sleep(0.5)
    
    if released:
        print(f"\n✅ Successfully released {len(released)} camera(s): {released}")
    else:
        print("\nℹ️  No cameras were in use")
    
    return released

if __name__ == "__main__":
    print("="*60)
    print("🎥 SmartRail Shield - Camera Release Utility")
    print("="*60)
    print()
    
    released = release_all_cameras()
    
    print()
    print("="*60)
    print("✨ Camera cleanup complete!")
    print("💡 You can now start any detection module")
    print("="*60)
    
    # Keep window open for a moment
    time.sleep(2)
