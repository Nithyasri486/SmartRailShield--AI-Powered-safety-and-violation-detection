import pyttsx3
import threading

def speak_text(text):
    """
    Speaks the provided text using pyttsx3 in a separate thread to avoid blocking.
    """
    def run_speech():
        try:
            engine = pyttsx3.init()
            # Set properties if needed
            engine.setProperty('rate', 150)    # Speed
            engine.setProperty('volume', 1.0)  # Volume
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            print(f"🔊 Voice Alert Error: {str(e)}")

    # Run in thread so the main app doesn't freeze
    speech_thread = threading.Thread(target=run_speech)
    speech_thread.start()
