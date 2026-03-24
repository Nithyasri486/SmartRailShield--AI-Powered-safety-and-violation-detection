from flask import Flask, jsonify
import threading
import time
import math
import os
import sys
from object import ObstacleDetector

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

app = Flask(__name__)

# -----------------------------
# GLOBAL STATE
# -----------------------------
current_location = {"lat": 13.0827, "lon": 80.2707}  # Chennai
current_speed_kmph = 80
obstacles = []
decision_state = {}

# -----------------------------
# DISTANCE FUNCTION
# -----------------------------
def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi / 2) ** 2 +
        math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

# -----------------------------
# RULE-BASED DECISION ENGINE
# -----------------------------
def evaluate_risk(distance_m, speed):
    if distance_m > 800:
        return "NORMAL", speed, False

    elif 500 < distance_m <= 800:
        return "MEDIUM", speed * 0.7, False

    elif 200 < distance_m <= 500:
        return "HIGH", speed * 0.4, False

    else:
        return "EMERGENCY", 0, True

# -----------------------------
# TRAIN MOVEMENT (SIMULATION)
# -----------------------------
def update_location():
    global current_location
    while True:
        current_location["lat"] += 0.00001
        current_location["lon"] += 0.00001
        time.sleep(3)

# -----------------------------
# OBSTACLE + DECISION THREAD
# -----------------------------
def obstacle_monitor(detector):
    global obstacles, current_speed_kmph, decision_state

    while True:
        detected, quit_flag = detector.get_obstacles(
            current_location=current_location,
            show_frame=False  # Disabled - use obstacle_streamlit.py for visual display
        )

        obstacles = detected

        nearest_dist = None
        nearest_obs = None

        for obs in obstacles:
            d_km = haversine_distance(
                current_location["lat"],
                current_location["lon"],
                obs["lat"],
                obs["lon"]
            )
            d_m = d_km * 1000

            if nearest_dist is None or d_m < nearest_dist:
                nearest_dist = d_m
                nearest_obs = obs

        if nearest_dist is not None:
            zone, new_speed, emergency = evaluate_risk(
                nearest_dist, current_speed_kmph
            )

            decision_state = {
                "zone": zone,
                "distance_m": round(nearest_dist, 2),
                "current_speed": round(current_speed_kmph, 2),
                "recommended_speed": round(new_speed, 2),
                "emergency_brake": emergency,
                "obstacle": nearest_obs["class"]
            }

            current_speed_kmph = new_speed
            print("DECISION:", decision_state)
            
            # Save to Firebase if risk is high or emergency
            if zone in ["HIGH", "EMERGENCY"]:
                if FIREBASE_ENABLED and firebase_manager:
                    try:
                        obstacle_data = {
                            'module': 'obstacle_detection',
                            'object_class': nearest_obs["class"],
                            'distance_meters': round(nearest_dist, 2),
                            'zone': zone,
                            'emergency_brake': emergency,
                            'current_speed': round(current_speed_kmph, 2),
                            'mode': 'flask_app'
                        }
                        firebase_manager.save_obstacle_detection(obstacle_data)
                    except Exception as e:
                        print(f"⚠️ Failed to save to Firebase: {str(e)}")

        if quit_flag:
            break

        time.sleep(0.5)

# -----------------------------
# FLASK ROUTES
# -----------------------------
@app.route("/")
def index():
    return jsonify({"status": "Railway Obstacle System Running"})

@app.route("/status")
def status():
    return jsonify({
        "location": current_location,
        "speed_kmph": current_speed_kmph,
        "decision": decision_state,
        "obstacles": obstacles
    })

# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    detector = ObstacleDetector("best.pt")

    threading.Thread(target=update_location, daemon=True).start()
    threading.Thread(
        target=obstacle_monitor,
        args=(detector,),
        daemon=True
    ).start()

    try:
        app.run(debug=False, use_reloader=False)
    finally:
        detector.release()
