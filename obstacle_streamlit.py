import torch
import torch.nn as nn
import os
import sys

# CRITICAL FIX for PyTorch 2.6+ "Weights only load failed" error
os.environ["TORCH_LOAD_WEIGHTS_ONLY"] = "0"

# Add safe globals for model loading
try:
    from ultralytics.nn.tasks import DetectionModel
    if hasattr(torch.serialization, 'add_safe_globals'):
        torch.serialization.add_safe_globals([DetectionModel, nn.Sequential])
except Exception:
    pass

import streamlit as st
import cv2
import numpy as np
import pandas as pd
from ultralytics import YOLO
import time
from PIL import Image
import folium
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go

# Add parent directory to path for Firebase import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Simulated Train GPS (Starting point: e.g., Chennai)
TRAIN_LAT = 13.0827
TRAIN_LON = 80.2707

# --- Initial Setup ---
if 'firebase_initialized' not in st.session_state:
    try:
        # Remove any cached local firebase_config
        if 'firebase_config' in sys.modules:
            del sys.modules['firebase_config']
        from firebase_config import firebase_manager
        firebase_manager.initialize()
        st.session_state.firebase_initialized = firebase_manager.initialized
    except Exception as e:
        st.session_state.firebase_initialized = False

from firebase_config import firebase_manager
FIREBASE_ENABLED = st.session_state.firebase_initialized

# Page config
st.set_page_config(
    page_title="Obstacle Detection",
    page_icon="🚧",
    layout="wide"
)


# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        padding: 1rem;
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    .detection-box {
        padding: 1.5rem;
        border-radius: 10px;
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        color: white;
        text-align: center;
        font-size: 1.2rem;
        font-weight: bold;
        margin: 1rem 0;
    }
    .obstacle-alert {
        background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        font-weight: bold;
        animation: pulse 1s infinite;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
</style>
""", unsafe_allow_html=True)

# Title
st.markdown('<div class="main-header">🚧 SmartRail Shield - Obstacle Detection</div>', unsafe_allow_html=True)

# Load YOLO model
@st.cache_resource
def load_model(model_type="COCO Model (Pre-trained)"):
    """Initialize and Setup the COCO Model"""
    try:
        with st.spinner(f"🚀 Initializing {model_type}... Setting up COCO Dataset weights..."):
            # Use the Nano model (yolov8n.pt) for better memory efficiency
            # It uses ~1/4 the memory of yolov8s.pt with comparable performance
            model = YOLO("yolov8n.pt") 
            time.sleep(1) # Visual feedback for "Setup"
        st.sidebar.success(f"✅ {model_type} Trained & Ready!")
        return model
    except Exception as e:
        st.error(f"❌ Error during Model Setup: {str(e)}")
        st.stop()

# Auto-initialize COCO model for maximum accuracy
model = load_model()

# List COCO classes for user
with st.sidebar.expander("🔍 COCO Dataset Detectables"):
    if model:
        st.write("Model identifies 80 objects including:")
        st.write("Person, Train, Truck, Car, Cow, Dog, Horse, Elephant, Zebra, Bear, etc.")

# Session state initialization
if 'detection_history' not in st.session_state:
    st.session_state.detection_history = []
if 'total_detections' not in st.session_state:
    st.session_state.total_detections = 0
if 'current_obstacles' not in st.session_state:
    st.session_state.current_obstacles = []
if 'detection_running' not in st.session_state:
    st.session_state.detection_running = False
if 'persistent_obstacles' not in st.session_state:
    st.session_state.persistent_obstacles = {}

# Sidebar controls
st.sidebar.header("⚙️ Settings")

# --- Firebase Status ---
st.sidebar.subheader("🔥 Firebase Status")
if FIREBASE_ENABLED:
    st.sidebar.success("Connected to Central DB ✅")
else:
    st.sidebar.error("Disconnected / Offline ❌")
    if st.sidebar.button("🔄 Reload & Reconnect"):
        st.session_state.clear()
        st.rerun()

camera_index = st.sidebar.selectbox("Camera Source", [0, 1, 2], index=0)
st.sidebar.info("💡 Tip: Close other modules before starting to free up the camera.")
confidence_threshold = st.sidebar.slider("Detection Confidence", 0.1, 1.0, 0.3, 0.05, 
                                        help="Lower confidence to detect more animals/objects")
show_labels = st.sidebar.checkbox("Show Labels", value=True)
show_confidence = st.sidebar.checkbox("Show Confidence Score", value=True)

# List detectable classes for user awareness
with st.sidebar.expander("🔍 Detectable Objects"):
    if model:
        classes = list(model.names.values())
        st.write(", ".join(classes))

# --- Helper Functions ---
def send_consolidated_alert(new_obstacles):
    """Sends a single email for multiple detected obstacles"""
    from email_utils import send_email_alert
    
    count = len(new_obstacles)
    # Determine the most critical alert type
    classes = [o['class'].lower() for o in new_obstacles]
    
    if any('person' in c for c in classes):
        subject = f"🚨 URGENT: PERSON & {count-1} others on Track!" if count > 1 else "🚨 URGENT: PERSON on Track!"
    elif any('animal' in c for c in classes) or any('horse' in c for c in classes):
        subject = f"🐄 ANIMAL ALERT: Multiple Obstacles ({count})" if count > 1 else f"🐄 ANIMAL ALERT: {new_obstacles[0]['class']}"
    else:
        subject = f"🚧 Obstacle Alert: {count} Objects Detected"

    body = f"""
    Attention Control Room,

    Multiple obstacles have been detected on the railway tracks simultaneously.

    --- Summary of Detections ---
    Total Objects: {count}
    Time: {time.strftime("%Y-%m-%d %H:%M:%S")}

    --- Items List ---
    """
    for i, obs in enumerate(new_obstacles, 1):
        obj_lat = TRAIN_LAT + (obs['distance'] * 0.000009)
        body += f"{i}. {obs['class'].upper()} at {obs['distance']}m (Est: Lat {obj_lat:.5f})\n"

    body += "\nAction: Please notify the pilot immediately and verify via live feed."
    
    if send_email_alert(subject, body):
        st.toast(f"📧 Consolidated Alert Sent ({count} objects)", icon="🚀")

# Debug connection
if st.sidebar.checkbox("🐞 Debug Connection"):
    st.sidebar.write(f"Config File: {os.path.abspath('firebase_config.py')}")
    st.sidebar.write(f"Key File exists: {os.path.exists('firebase_key.json')}")
    if firebase_manager:
        st.sidebar.write(f"Firebase Manager Init: {firebase_manager.initialized}")

# Main layout
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📹 Live Camera Feed")
    video_placeholder = st.empty()

with col2:
    st.subheader("🎯 Detection Status")
    status_placeholder = st.empty()
    
    st.subheader("📊 Statistics")
    metrics_col1, metrics_col2 = st.columns(2)
    with metrics_col1:
        total_count = st.empty()
    with metrics_col2:
        current_count = st.empty()
    
    st.subheader("🗺️ Obstacle Track Map")
    map_placeholder = st.empty()
    
    st.subheader("📊 Track Distance View")
    chart_placeholder = st.empty()

    st.subheader("📋 Recent Detections")
    history_placeholder = st.empty()

# Control buttons
col_btn1, col_btn2, col_btn3 = st.columns(3)
with col_btn1:
    start_btn = st.button("▶️ Start Detection", type="primary", use_container_width=True, disabled=st.session_state.detection_running)
with col_btn2:
    stop_btn = st.button("⏹️ Stop Detection", use_container_width=True, disabled=not st.session_state.detection_running)
with col_btn3:
    if st.button("🔄 Reset Camera", use_container_width=True):
        st.session_state.detection_running = False
        time.sleep(0.5)
        st.rerun()

if start_btn:
    st.session_state.detection_running = True
    st.rerun()
    
if stop_btn:
    st.session_state.detection_running = False
    st.rerun()

# Main detection loop
if st.session_state.detection_running:
    # Try to open camera with explicit settings
    cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    
    if not cap.isOpened():
        st.error("❌ Unable to open camera. Please check your camera connection or try a different camera source.")
        st.warning("💡 Tip: If another module is using the camera, stop that module first or click 'Reset Camera'")
        st.session_state.detection_running = False
    else:
        st.success("✅ Camera started successfully!")
        
        # Run detection in a loop
        frame_count = 0
        import gc
        
        # Ensure persistence dictionary exists
        if 'persistent_obstacles' not in st.session_state:
            st.session_state.persistent_obstacles = {}
        
        try:
            status_placeholder.info("🔄 Initializing Camera... Please wait.")
            while st.session_state.detection_running:
                ret, frame = cap.read()
                if not ret:
                    st.error("❌ Failed to read from camera")
                    break
                
                # Run YOLO detection
                results = model.predict(frame, conf=confidence_threshold, verbose=False)
                
                obstacles_detected = []
                
                # Get frame dimensions for distance calculation
                frame_height = frame.shape[0]
                
                # Process detections
                for result in results:
                    for box in result.boxes:
                        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                        conf = float(box.conf[0])
                        cls = int(box.cls[0])
                        class_name = model.names.get(cls, "Unknown")
                        
                        # Calculate estimated distance (based on object height in frame)
                        # Rough estimation: distance (m) ≈ (known_height / pixel_height) * focal_length
                        # Simplified: larger objects are closer
                        box_height = y2 - y1
                        box_area = (x2 - x1) * (y2 - y1)
                        
                        # Rough distance estimation (inverse relationship with size)
                        # Assumes objects at ~50m when they fill 10% of frame
                        size_ratio = box_area / (frame.shape[0] * frame.shape[1])
                        estimated_distance = int(50 / (size_ratio * 10 + 0.1))  # meters
                        estimated_distance = min(estimated_distance, 999)  # Cap at 999m
                        
                        # Animal-specific highlighting (Case insensitive match)
                        target_animal_classes = ['animal', 'cow', 'dog', 'elephant', 'vessel', 'person']
                        is_animal = any(a in class_name.lower() for a in target_animal_classes) or (cls == 0) # 0 is Animal in best.pt
                        
                        if is_animal or estimated_distance < 100:
                            box_color = (0, 0, 255)  # Red - DANGER
                            text_bg_color = (0, 0, 200)
                            display_text = f"⚠️ {class_name.upper()} !!" if is_animal else "⚠️ DANGER"
                            cv2.putText(frame, display_text, (x1, y2 + 30), 
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                        elif estimated_distance < 300:
                            box_color = (0, 165, 255)  # Orange - WARNING
                            text_bg_color = (0, 140, 200)
                        else:
                            box_color = (0, 255, 0)  # Green - SAFE
                            text_bg_color = (0, 200, 0)
                        
                        # Draw bounding box
                        cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 3)
                        
                        # Draw label with distance
                        if show_labels:
                            label = f"{class_name} ~{estimated_distance}m"
                            if show_confidence:
                                label = f"{class_name} {conf:.2f} ~{estimated_distance}m"
                            
                            # Background for text
                            (text_width, text_height), _ = cv2.getTextSize(
                                label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2
                            )
                            cv2.rectangle(
                                frame, 
                                (x1, y1 - text_height - 10), 
                                (x1 + text_width + 10, y1), 
                                text_bg_color, 
                                -1
                            )
                            cv2.putText(
                                frame, 
                                label, 
                                (x1 + 5, y1 - 5),
                                cv2.FONT_HERSHEY_SIMPLEX, 
                                0.7, 
                                (255, 255, 255), 
                                2
                            )
                        
                        obstacles_detected.append({
                            'class': class_name,
                            'confidence': conf,
                            'distance': estimated_distance,
                            'timestamp': time.strftime("%H:%M:%S")
                        })
                
                # --- Persistence Mechanism (Robust) ---
                # Reduce cooldown
                for key in list(st.session_state.persistent_obstacles.keys()):
                    st.session_state.persistent_obstacles[key]['cooldown'] -= 1
                    if st.session_state.persistent_obstacles[key]['cooldown'] <= 0:
                        del st.session_state.persistent_obstacles[key]

                # Update/Add current detections
                for obs in obstacles_detected:
                    # Use a unique ID based on class and approximate distance to track multiple objects
                    obj_id = f"{obs['class']}_{obs['distance'] // 10}" 
                    st.session_state.persistent_obstacles[obj_id] = {
                        'data': obs,
                        'cooldown': 200 # Visible for ~10-15 seconds even if missed
                    }

                # Get the list of all persistent obstacles to display
                display_obstacles = [item['data'] for item in st.session_state.persistent_obstacles.values()]
                st.session_state.current_obstacles = display_obstacles
                
                # Only count NEW obstacles (not in current frame continuously)
                # Create a simple tracking mechanism
                current_frame_objects = set()
                if obstacles_detected:
                    for obs in obstacles_detected:
                        # Create a simple identifier (class + rough position area)
                        obj_id = f"{obs['class']}_{obs['distance']//50}"  # Group by class and distance zone
                        current_frame_objects.add(obj_id)
                    
                    # Only increment count if this is a NEW detection session
                    # (i.e., if we had no obstacles before, or different objects)
                    if not hasattr(st.session_state, 'last_frame_objects'):
                        st.session_state.last_frame_objects = set()
                        st.session_state.total_detections += len(obstacles_detected)
                        
                        # Save ALL initial obstacles to Firebase and send consolidated email
                        if FIREBASE_ENABLED and firebase_manager:
                            new_obs_list = []
                            for obs in obstacles_detected:
                                try:
                                    obstacle_data = {
                                        'module_name': 'Obstacle Detection',
                                        'object': obs['class'],
                                        'distance': obs['distance'],
                                        'confidence': float(obs['confidence']),
                                        'status': 'INITIAL_DETECTION'
                                    }
                                    firebase_manager.push_to_realtime('obstacle_detections', obstacle_data)
                                    new_obs_list.append(obs)
                                except Exception as e:
                                    print(f"⚠️ Failed to save to Firebase: {str(e)}")
                            
                            if new_obs_list:
                                # Send consolidated email for initial detection
                                send_consolidated_alert(new_obs_list)
                    else:
                        # Only count NEW objects that weren't in last frame
                        new_objects = current_frame_objects - st.session_state.last_frame_objects
                        if new_objects:
                            st.session_state.total_detections += len(new_objects)
                            
                            # Collect NEW obstacles for consolidated alert
                            new_obs_to_alert = []
                            if FIREBASE_ENABLED and firebase_manager:
                                for obs in obstacles_detected:
                                    obj_id = f"{obs['class']}_{obs['distance']//50}"
                                    if obj_id in new_objects:
                                        try:
                                            # GPS Calculation
                                            obj_lat = TRAIN_LAT + (obs['distance'] * 0.000009)
                                            obj_lon = TRAIN_LON + (np.random.uniform(-0.0001, 0.0001))
                                            
                                            obstacle_data = {
                                                'module_name': 'Obstacle Detection',
                                                'object': obs['class'],
                                                'distance': obs['distance'],
                                                'confidence': float(obs['confidence']),
                                                'status': 'NEW_OBJECT_ALERT',
                                                'latitude': obj_lat,
                                                'longitude': obj_lon
                                            }
                                            firebase_manager.push_to_realtime('obstacle_detections', obstacle_data)
                                            new_obs_to_alert.append(obs)
                                            
                                            # --- Voice Alert (Trigger immediately) ---
                                            from voice_utils import speak_text
                                            if 'train' in obs['class'].lower():
                                                speak_text(f"Attention, train is coming at {obs['distance']} meters.")
                                            elif 'person' in obs['class'].lower() or 'animal' in obs['class'].lower():
                                                speak_text(f"Danger! {obs['class']} detected on the track.")
                                            
                                        except Exception as e:
                                            print(f"⚠️ Firebase/Voice failed: {str(e)}")
                                
                                # Send ONE consolidated email for all new objects in this frame
                                if new_obs_to_alert:
                                    send_consolidated_alert(new_obs_to_alert)
                    
                    st.session_state.last_frame_objects = current_frame_objects
                    
                    # Add to history (keep last 10) - only add if truly new
                    for obs in obstacles_detected:
                        # Only add to history if this exact detection is new
                        if not st.session_state.detection_history or obs != st.session_state.detection_history[0]:
                            st.session_state.detection_history.insert(0, obs)
                    if len(st.session_state.detection_history) > 10:
                        st.session_state.detection_history = st.session_state.detection_history[:10]
                else:
                    # Clear tracking when no obstacles
                    if hasattr(st.session_state, 'last_frame_objects'):
                        st.session_state.last_frame_objects = set()
                
                # Display frame
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                video_placeholder.image(frame_rgb, channels="RGB", use_container_width=True)
                
                # Update metrics
                total_count.metric("Total Detections", st.session_state.total_detections)
                current_count.metric("Current Obstacles", len(display_obstacles))
                
                # Update status
                if display_obstacles:
                    # Find nearest obstacle
                    nearest = min(display_obstacles, key=lambda x: x['distance'])
                    obstacle_list = ", ".join([f"{obs['class']} ({obs['distance']}m)" for obs in display_obstacles])
                    status_placeholder.markdown(
                        f'<div class="obstacle-alert">⚠️ OBSTACLES DETECTED: {obstacle_list}<br/>'
                        f'<span style="font-size:1.5rem;">⚡ NEAREST: {nearest["class"]} at {nearest["distance"]}m</span></div>',
                        unsafe_allow_html=True
                    )
                else:
                    status_placeholder.markdown(
                        '<div class="detection-box">✅ No Obstacles - Track Clear</div>',
                        unsafe_allow_html=True
                    )

                # --- Real-time Map Visualization (Fast Plotly MapBox) ---
                # This replaces Folium inside the loop for much better performance
                map_data = []
                # Always add Train
                map_data.append({
                    'Latitude': TRAIN_LAT,
                    'Longitude': TRAIN_LON,
                    'Object': '🚅 TRAIN (YOU)',
                    'Distance': 0,
                    'Size': 20,
                    'Color': 'blue'
                })
                
                # Add persistent obstacles
                for obs in display_obstacles:
                    o_lat = TRAIN_LAT + (obs['distance'] * 0.000009)
                    o_lon = TRAIN_LON + 0.00002
                    map_data.append({
                        'Latitude': o_lat,
                        'Longitude': o_lon,
                        'Object': f"⚠️ {obs['class'].upper()}",
                        'Distance': obs['distance'],
                        'Size': 15,
                        'Color': 'red'
                    })
                
                df_map = pd.DataFrame(map_data)
                
                # Update Map & Charts less frequently to save memory (every 10th frame)
                if frame_count % 10 == 0:
                    # Plotly MapBox is interactive and much faster than Folium in a loop
                    fig_map = px.scatter_mapbox(
                        df_map, 
                        lat="Latitude", 
                        lon="Longitude", 
                        text="Object", 
                        color="Color",
                        color_discrete_map={"blue": "#2E86C1", "red": "#E74C3C"},
                        size="Size",
                        zoom=15,
                        height=400
                    )
                    
                    fig_map.update_layout(
                        mapbox_style="open-street-map",
                        margin={"r":0,"t":0,"l":0,"b":0},
                        showlegend=False
                    )
                    
                    # Update Map Placeholder
                    map_placeholder.plotly_chart(fig_map, use_container_width=True, key="obstacle_map_display")
                    
                    # Periodic Garbage Collection
                    gc.collect()
                
                # Update metrics
                total_count.metric("Total Detections", st.session_state.total_detections)
                current_count.metric("Current Obstacles", len(obstacles_detected))
                
                # Update history
                if st.session_state.detection_history:
                    history_html = "<div style='background: #f0f2f6; padding: 1rem; border-radius: 10px;'>"
                    for i, obs in enumerate(st.session_state.detection_history[:5], 1):
                        # Color code based on distance
                        if obs['distance'] < 100:
                            dist_color = '#ff0000'  # Red
                        elif obs['distance'] < 300:
                            dist_color = '#ff8800'  # Orange
                        else:
                            dist_color = '#00aa00'  # Green
                        
                        history_html += f"<div style='padding: 0.5rem; border-bottom: 1px solid #ddd;'>"
                        history_html += f"<strong>{i}.</strong> {obs['class']} "
                        history_html += f"<span style='color: {dist_color}; font-weight: bold;'>~{obs['distance']}m</span> "
                        history_html += f"<span style='color: #666;'>({obs['confidence']:.2f})</span> "
                        history_html += f"<span style='color: #999; float: right;'>{obs['timestamp']}</span>"
                        history_html += "</div>"
                    history_html += "</div>"
                    history_placeholder.markdown(history_html, unsafe_allow_html=True)
                else:
                    history_placeholder.info("No detections yet")
                
                # Small delay
                time.sleep(0.03)
                frame_count += 1
        except Exception as e:
            st.error(f"❌ Error during detection: {str(e)}")
        finally:
            # Always release camera
            if cap is not None and cap.isOpened():
                cap.release()
                cv2.destroyAllWindows()
            st.info("⏹️ Detection stopped - Camera released")

# Instructions
with st.expander("ℹ️ How to Use"):
    st.markdown("""
    ### Instructions:
    1. **Click "Start Detection"** to begin monitoring
    2. The system will detect obstacles on railway tracks in real-time
    3. Detected obstacles will be highlighted with bounding boxes
    4. **Adjust confidence threshold** in the sidebar to filter detections
    5. **Click "Stop Detection"** to end the session
    
    ### Features:
    - ✅ Real-time YOLO-based object detection
    - ✅ Customizable confidence threshold
    - ✅ Detection history and statistics
    - ✅ Visual alerts for obstacles
    - ✅ Multiple camera support
    
    ### Safety Tips:
    - Ensure good lighting for better detection
    - Position camera to have clear view of tracks
    - Adjust confidence threshold based on environment
    - Monitor the detection feed continuously
    
    ### Troubleshooting:
    - If camera doesn't open, try changing camera source in sidebar
    - Lower confidence threshold for more detections (may include false positives)
    - Higher confidence threshold for fewer, more accurate detections
    """)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>SmartRail Shield - Obstacle Detection Module v2.0</div>",
    unsafe_allow_html=True
)
