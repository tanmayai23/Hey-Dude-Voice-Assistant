"""Hey Dude / Jarvis main app entrypoint.

Designed for low-RAM laptops:
- Heavy modules (cv2, pywhatkit, pyaudio) are imported lazily inside
  feature functions, not at startup.
- Continuous hotword listening is OFF by default (set ENABLE_HOTWORD=true
  in .env to turn it on). Click-to-talk in the UI works without it.
"""
import os
import sys
import eel
import threading
import warnings

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning, module="eel")

from dotenv import load_dotenv
load_dotenv()

# Import only what's needed at startup. Feature modules self-import on first call.
from Backend.command import speak_text, takecommand, allCommands, start_listen  # noqa: F401
from Backend.features import playassistantsound  # noqa: F401
import Backend.config  # noqa: F401  - registers @eel.expose handlers


def _open_browser():
    """Open the assistant UI in the user's browser. Try Edge in app mode first
    (looks like a native app), fall back to default browser if Edge is missing."""
    url = "http://localhost:8006/Frontend/index.html"
    edge_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    for edge in edge_paths:
        if os.path.exists(edge):
            os.system(f'start "" "{edge}" --app="{url}"')
            return
    import webbrowser
    webbrowser.open(url)


def start():
    eel.init('Frontend')

    @eel.expose
    def get_app_info():
        return {'name': 'Hey Dude', 'version': '1.0.0', 'status': 'Ready'}

    @eel.expose
    def close_app():
        os._exit(0)

    @eel.expose
    def play_sound(sound_file):
        try:
            from playsound import playsound

            def _play():
                playsound(sound_file)

            t = threading.Thread(target=_play, daemon=True)
            t.start()
            return {"status": "success", "message": f"Playing {sound_file}"}
        except ImportError:
            return {"status": "error", "message": "playsound not installed"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @eel.expose
    def debug_send_test(text="Hello from backend (debug)"):
        try:
            eel.receiveRecognitionResult(text)()
            return {"status": "ok", "sent": text}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    # Optional: continuous "Hey Dude" hotword listener. Off by default — costs
    # network + RAM (polls Google Speech API every few seconds).
    if os.getenv('ENABLE_HOTWORD', 'false').lower() == 'true':
        def _hotword_worker():
            try:
                from hotword_detection import listen_for_hotword
                print("\n🎤 Hotword detection enabled — say 'Hey Dude' to activate.\n")
                listen_for_hotword(eel)
            except Exception as e:
                print(f"❌ Hotword detection error: {e}")

        threading.Thread(target=_hotword_worker, daemon=True).start()
    else:
        print("ℹ️  Hotword detection OFF (set ENABLE_HOTWORD=true in .env to enable). "
              "Click the mic in the UI to talk.")

    print("=" * 50)
    print("🎙️  Hey Dude Voice Assistant Started — http://localhost:8006")
    print("=" * 50)

    try:
        threading.Thread(target=playassistantsound, daemon=True).start()
    except Exception:
        pass

    _open_browser()
    eel.start('index.html', mode=None, host='localhost', port=8006, block=True)
