# Camera Management Guide - SmartRail Shield

## Problem
உங்களுக்கு 3 camera-based modules இருக்கு:
1. **Drowsiness Detection** - drows_streamlit.py
2. **License Plate Recognition** - np_streamlit.py  
3. **Obstacle Detection** - obstacle_streamlit.py

**Issue**: When you run multiple modules simultaneously, only the FIRST module gets camera access. Other modules show a **black screen** because Windows allows only ONE application to access a camera at a time.

## Solution Applied

### What We Fixed:

1. **Added Reset Camera Button** 🔄
   - Each module now has a "Reset Camera" button
   - This releases the camera immediately
   
2. **Proper Camera Cleanup** ✅
   - Camera is now properly released when:
     - You click Stop Detection
     - An error occurs
     - Module switches tabs
   - Added `try-except-finally` blocks to ensure cleanup

3. **Better Error Messages** 💡
   - Now shows helpful tips when camera can't be accessed
   - Suggests stopping other modules first

4. **Session State Management** 🔄
   - Each module tracks if it's running
   - Prevents multiple starts

## How to Use Multiple Modules

### Option 1: Use One at a Time (Recommended)
```
1. Start Module A → Use it → Click "Stop Detection"
2. Wait 1 second
3. Start Module B → Use it → Click "Stop Detection"
4. Continue...
```

### Option 2: Use Reset Camera
```
1. If Module B shows black screen
2. Click "Reset Camera" button on Module B
3. Click "Start Detection" again
```

### Option 3: Use Different Cameras
If you have multiple webcams connected:
```
1. Module A → Camera Source: 0
2. Module B → Camera Source: 1
3. Module C → Camera Source: 2
```

## Emergency Camera Release

If camera is stuck, run this command:
```bash
python release_cameras.py
```

This will:
- Release all camera resources (Camera 0, 1, 2)
- Close all OpenCV windows
- Allow fresh start

## Best Practices

### ✅ DO:
- **Stop one module before starting another**
- **Use the "Reset Camera" button if camera fails**
- **Check sidebar for camera source selection**
- **Wait 1-2 seconds between switching modules**

### ❌ DON'T:
- Don't run all 3 modules simultaneously with same camera
- Don't force close Streamlit (use Stop button first)
- Don't switch modules without stopping current one

## Troubleshooting

### Problem: Black Screen in Camera Feed
**Solution:**
1. Click "⏹️ Stop Detection" on ALL modules
2. Click "🔄 Reset Camera"
3. Wait 2 seconds
4. Click "▶️ Start Detection" again

### Problem: "Unable to open camera" Error
**Solution:**
1. Check if another module is running → Stop it
2. Run `python release_cameras.py`
3. Try different camera source in sidebar (0, 1, or 2)
4. Restart the dashboard app

### Problem: Camera Works for First Module Only
**Solution:**
- **This is expected behavior!** 
- Stop the first module before starting second one
- OR use different camera sources for each module

## Technical Details

### Changes Made:

**File: drows_streamlit.py (Lines 134-169, 238-249)**
- Added reset camera button
- Added try-except-finally for cleanup
- Added session state management
- Reduced max_frames to 500 for faster response

**File: np_streamlit.py (Lines 154-196, 262-278)**
- Same improvements as above
- Proper camera release on stop

**File: obstacle_streamlit.py (Lines 115-159, 281-296)**
- Same improvements as above
- Proper camera release with cv2.destroyAllWindows()

### Camera Settings Applied:
```python
cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduces lag
```

## Running the Dashboard

```bash
# Start the dashboard
python dashboard_app.py

# Open browser
http://localhost:5000

# Launch modules one at a time
# Always stop before switching!
```

## Summary

🎯 **Key Point**: Windows allows only ONE camera access at a time.

✅ **Solution**: Stop one module before starting another, or use different cameras.

🔄 **Quick Fix**: Use the "Reset Camera" button if issues occur.

---
**Last Updated**: 2026-01-29
**Version**: 2.0 with Camera Management
