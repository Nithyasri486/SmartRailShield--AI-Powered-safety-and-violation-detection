import os
import sys
import subprocess
import time


# ============================================================
# Utility: Run Streamlit App (Machine Fault Module)
# ============================================================
def run_streamlit_app(file_path):
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False

    print("🌐 Streamlit Machine Fault UI starting...")
    print("👉 After prediction, press CTRL+C in terminal to stop Streamlit and continue.\n")

    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", file_path], check=False)
    except KeyboardInterrupt:
        print("\n✅ Streamlit stopped by user. Continuing to next module...\n")
        return True

    return True


# ============================================================
# Utility: Run normal Python Script (Drowsiness / ANPR)
# ============================================================
def run_python_script(file_path, title="MODULE"):
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False

    print(f"▶ Running {title}: {file_path}\n")

    try:
        result = subprocess.run([sys.executable, file_path], check=False)
        if result.returncode != 0:
            print(f"❌ {title} failed (return code: {result.returncode})\n")
            return False
    except KeyboardInterrupt:
        print(f"\n⚠️ {title} stopped by user.\n")
        return True

    print(f"✅ {title} completed.\n")
    return True


# ============================================================
# Utility: Run Flask App (Obstacle Detection)
# ============================================================
def run_flask_app(file_path, title="FLASK MODULE"):
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False

    print(f"▶ Running {title}: {file_path}")
    print("👉 This will start Flask server.")
    print("👉 Press CTRL+C to stop Flask and continue to next module.\n")

    try:
        subprocess.run([sys.executable, file_path], check=False)
    except KeyboardInterrupt:
        print("\n✅ Flask stopped by user. Continuing to next module...\n")
        return True

    return True


# ============================================================
# MAIN FLOW
# ============================================================
def main():
    print("\n============================================================")
    print("🚆 SMART RAILSHIELD - INTEGRATED MAIN CONTROLLER")
    print("============================================================\n")

    base_dir = os.path.dirname(os.path.abspath(__file__))

    # ------------------ MODULE PATHS ------------------
    machine_file = os.path.join(base_dir, "fault detection", "machine.py")
    drowsy_file = os.path.join(base_dir, "Drowsiness", "drows.py")
    obstacle_file = os.path.join(base_dir, "obstacle", "app.py")
    anpr_file = os.path.join(base_dir, "licenseplate_recognisation", "np.py")

    # ==================================================
    # STEP 1: MACHINE FAULT (STREAMLIT)
    # ==================================================
    print("🔧 STEP 1: MACHINE FAULT DETECTION")
    print("--------------------------------------------------\n")
    ok1 = run_streamlit_app(machine_file)

    if not ok1:
        print("🛑 Stopping flow due to Machine Fault module error.\n")
        return

    # ==================================================
    # STEP 2: DROWSINESS (PYTHON)
    # ==================================================
    print("👁 STEP 2: PILOT DROWSINESS DETECTION")
    print("--------------------------------------------------")
    print("👉 Press 'q' inside camera window to close it and continue flow.\n")
    ok2 = run_python_script(drowsy_file, title="DROWSINESS DETECTION")

    if not ok2:
        print("🛑 Stopping flow due to Drowsiness module error.\n")
        return

    # ==================================================
    # STEP 3: OBSTACLE (FLASK)
    # ==================================================
    print("🚧 STEP 3: OBSTACLE DETECTION")
    print("--------------------------------------------------\n")
    ok3 = run_flask_app(obstacle_file, title="OBSTACLE DETECTION (FLASK + YOLO)")

    if not ok3:
        print("🛑 Stopping flow due to Obstacle module error.\n")
        return

    # ==================================================
    # STEP 4: ANPR (PYTHON)
    # ==================================================
    print("🚦 STEP 4: LEVEL CROSSING - NUMBER PLATE RECOGNITION (ANPR)")
    print("--------------------------------------------------")
    print("👉 Press 'q' inside video window to close it and finish.\n")
    ok4 = run_python_script(anpr_file, title="ANPR / LICENSE PLATE RECOGNITION")

    if not ok4:
        print("🛑 Stopping flow due to ANPR module error.\n")
        return

    print("============================================================")
    print("🎉 ALL MODULES COMPLETED SUCCESSFULLY!")
    print("============================================================\n")


# ============================================================
# RUN
# ============================================================
if __name__ == "__main__":
    main()
