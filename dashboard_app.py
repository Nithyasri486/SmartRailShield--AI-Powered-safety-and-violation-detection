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

from flask import Flask, render_template, request, jsonify
import subprocess
import threading

# Import Firebase configuration
try:
    from firebase_config import firebase_manager
    FIREBASE_ENABLED = firebase_manager.initialized
except ImportError:
    print("⚠️ Firebase not configured - Modules will run without cloud storage")
    FIREBASE_ENABLED = False
    firebase_manager = None

app = Flask(__name__)

# Get the base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Module paths
MODULES = {
    'fault': {
        'path': os.path.join(BASE_DIR, "fault detection", "machine.py"),
        'type': 'streamlit',
        'name': 'Machine Fault Detection'
    },
    'drowsiness': {
        'path': os.path.join(BASE_DIR, "Drowsiness", "drows_streamlit.py"),
        'type': 'streamlit',
        'name': 'Pilot Drowsiness Detection'
    },
    'obstacle': {
        'path': os.path.join(BASE_DIR, "obstacle", "obstacle_streamlit.py"),
        'type': 'streamlit',
        'name': 'Obstacle Detection'
    },
    'anpr': {
        'path': os.path.join(BASE_DIR, "licenceplate_recognisation", "np_streamlit.py"),
        'type': 'streamlit',
        'name': 'License Plate Recognition (ANPR)'
    }
}


def launch_module_async(module_info):
    """Launch a module in a separate process"""
    module_path = module_info['path']
    module_type = module_info['type']
    
    if not os.path.exists(module_path):
        print(f"❌ Module file not found: {module_path}")
        return
    
    # Get the directory containing the module
    module_dir = os.path.dirname(module_path)
    
    try:
        if module_type == 'streamlit':
            # Launch Streamlit app
            print(f"🌐 Launching Streamlit: {module_info['name']}")
            subprocess.Popen(
                [sys.executable, "-m", "streamlit", "run", module_path],
                cwd=module_dir,
                creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
            )
        elif module_type == 'flask':
            # Launch Flask app
            print(f"🌐 Launching Flask: {module_info['name']}")
            subprocess.Popen(
                [sys.executable, module_path],
                cwd=module_dir,
                creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
            )
        else:
            # Launch regular Python script
            print(f"▶ Launching Python: {module_info['name']}")
            subprocess.Popen(
                [sys.executable, module_path],
                cwd=module_dir,
                creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
            )
    except Exception as e:
        print(f"❌ Error launching {module_info['name']}: {str(e)}")


@app.route('/')
def index():
    """Render the dashboard"""
    return render_template('dashboard.html')


@app.route('/launch', methods=['POST'])
def launch():
    """Launch a specific module"""
    try:
        data = request.get_json()
        module_name = data.get('module')
        
        if not module_name or module_name not in MODULES:
            return jsonify({
                'success': False,
                'message': 'Invalid module name'
            }), 400
        
        module_info = MODULES[module_name]
        
        # Check if module file exists
        if not os.path.exists(module_info['path']):
            return jsonify({
                'success': False,
                'message': f"Module file not found: {module_info['path']}"
            }), 404
        
        # Launch module in a separate thread
        thread = threading.Thread(target=launch_module_async, args=(module_info,))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': f"{module_info['name']} launched successfully",
            'module': module_name
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/status')
def status():
    """Get status of all modules"""
    return jsonify({
        'modules': list(MODULES.keys()),
        'status': 'Dashboard running'
    })


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚆 SMARTRAILSHIELD DASHBOARD")
    print("="*60)
    
    # Firebase Status
    if FIREBASE_ENABLED:
        print("\n🔥 Firebase: CONNECTED ✅")
        print("   └─ Cloud storage enabled for all modules")
    else:
        print("\n⚠️  Firebase: OFFLINE")
        print("   └─ Modules will run without cloud storage")
        print("   └─ To enable: Place 'firebase-credentials.json' in project root")
    
    print("\n📊 Dashboard starting...")
    print("🌐 Open your browser and navigate to: http://localhost:5000")
    print("\n💡 Click on any module card to launch it")
    print("⌨️  Keyboard shortcuts: Ctrl+1, Ctrl+2, Ctrl+3, Ctrl+4")
    print("\n" + "="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
