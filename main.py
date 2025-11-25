import os
import eel
import threading
import warnings

# Suppress all DeprecationWarnings including pkg_resources
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning, module="eel")

from Backend.features import *
from Backend.command import *
  
# we do this beacuse we have to do multithreading
def start():
    eel.init('Frontend')
    
    @eel.expose
    def init():
        speak("Ready for Face Authentication")
        flag = recognize.AuthenticateFace()
        if flag == 1:
            speak("Authentication Successful. Starting Hey Dude Voice Assistant")
        else:
            speak("Authentication Failed. Exiting Application.")
    
    # Start hotword detection in background thread
    def start_hotword_detection():
        """Start hotword detection in a separate thread"""
        try:
            from hotword_detection import listen_for_hotword
            print("\n🎤 Starting Hotword Detection...")
            print("Say 'Hey Dude' to activate the assistant\n")
            listen_for_hotword(eel)  # Pass eel instance to hotword detection
        except Exception as e:
            print(f"❌ Hotword detection error: {e}")
    
    # Start hotword detection in daemon thread
    hotword_thread = threading.Thread(target=start_hotword_detection, daemon=True)
    hotword_thread.start()
        
    # Play startup sound when application starts
    print("="*50)
    print("🎙️  Hey Dude Voice Assistant Started")
    print("="*50)
    try:
        def play_startup_sound():
            playassistantsound()
        
        startup_thread = threading.Thread(target=play_startup_sound)
        startup_thread.daemon = True
        startup_thread.start()
    except Exception as e:
        pass

    # Add Python functions to be called from JavaScript
    @eel.expose
    def get_app_info():
        return {
            'name': '',
            'version': '1.0.0',
            'status': 'Ready'
        }

    @eel.expose
    def close_app():
        """Function to close the application"""
        import sys
        sys.exit()

    @eel.expose
    def play_sound(sound_file):
        """Function to play sound files"""
        try:
            # Import playsound here to avoid startup errors
            from playsound import playsound
            
            # Play sound in a separate thread to avoid blocking
            def play_in_thread():
                playsound(sound_file)
            
            thread = threading.Thread(target=play_in_thread)
            thread.daemon = True
            thread.start()
            return {"status": "success", "message": f"Playing {sound_file}"}
        except ImportError:
            return {"status": "error", "message": "Playsound library not found. Install with: pip install playsound==1.2.2"}
        except Exception as e:
            return {"status": "error", "message": str(e)}


    # Debug helper: send a test recognition result from Python to the frontend
    @eel.expose
    def debug_send_test(text="Hello from backend (debug)"):
        """Send a test message to the frontend's receiveRecognitionResult handler.

        Returns a status dict so the frontend can confirm the RPC succeeded.
        """
        try:
            # Call the JS function exposed as receiveRecognitionResult
            eel.receiveRecognitionResult(text)()
            return {"status": "ok", "sent": text}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    # Start the Eel server and open browser automatically in Edge app mode
    os.system('start msedge.exe --app="http://localhost:8006"')
    eel.start('index.html', mode=None, host='localhost', port=8006, block=True)



        
