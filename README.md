# SmartRailShield--AI-Powered-safety-and-violation-detection
**Project Overview**
- **Elevator pitch:** SmartRailShield is a real-time rail-safety system that detects obstacles, monitors driver drowsiness, recognizes license plates, and sends alerts via email/Firebase — with a web/dashboard interface for monitoring and playback.

**Description**
- SmartRailShield combines YOLO-based object detection, ANPR, drowsiness detection, and alerting to provide an integrated solution for railway/crossing safety. It ingests live camera streams or video files, detects hazards and people, logs events, and notifies operators through email and Firebase while offering a dashboard for visualization and review.

**Key Features**
- **Real-time object & obstacle detection:** YOLO models for fast detection and classification.
- **License plate recognition (ANPR):** Extracts and logs plate data from camera feeds.
- **Drowsiness detection:** Monitors driver/operator fatigue with webcam analysis.
- **Alerts & notifications:** Email and Firebase push alerts for critical events.
- **Dashboard & UI:** Web/Streamlit dashboard for live view, event history, and controls.
- **Modular codebase:** Separate modules for obstacle detection, ANPR, drowsiness, and integrations.

**Project Structure (high-level)**
- **Detection & models:** obstacle, `best.pt`, yolov8s.pt
- **ANPR:** licenceplate_recognisation
- **Drowsiness:** Drowsiness
- **Dashboard & frontend:** templates, static
- **Integrations & utilities:** firebase_config.py, email_utils.py, voice_utils.py, main_controller.py

**Quick Start**
- Install requirements and run the main controller:
  - `pip install -r requirements.txt`
  - `python main_controller.py`
- Open the dashboard (Streamlit / web) as documented in HOW_TO_RUN.md.
