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
    # Eel serves Frontend/ as web root, so index is at /index.html (not /Frontend/index.html).
    url = "http://localhost:8006/index.html"
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

    @eel.expose
    def reset_chat():
        """Expose reset at startup so UI hooks are always available.
        Gemini module is imported lazily only when reset is requested."""
        try:
            from Backend.gemini_ai import reset_chat as _reset_chat
            return _reset_chat()
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @eel.expose
    def get_system_stats():
        """Snapshot of RAM/CPU/Battery/Volume — polled by the dock overlay every 5s."""
        try:
            from Backend.system_control import get_stats
            return get_stats()
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @eel.expose
    def run_cleanup():
        """Triggered when the user clicks 'Haan' on a high-RAM toast."""
        try:
            from Backend.system_control import cleanup_caches
            r = cleanup_caches(confirm=True)
            try:
                eel.systemAlertResolved(r)()
            except Exception:
                pass
            return r
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @eel.expose
    def health():
        """Quick per-subsystem status for the dock indicator."""
        out = {"mic": "unknown", "gemini": "unknown",
               "porcupine": "unknown", "system_control": "unknown"}
        try:
            import speech_recognition  # noqa: F401
            out["mic"] = "ok"
        except Exception:
            out["mic"] = "unavailable"
        try:
            import google.generativeai  # noqa: F401
            out["gemini"] = "ok" if os.getenv("GEMINI_API_KEY") else "unavailable"
        except Exception:
            out["gemini"] = "unavailable"
        try:
            import pvporcupine  # noqa: F401
            out["porcupine"] = "ok" if os.getenv("PICOVOICE_ACCESS_KEY") else "unavailable"
        except Exception:
            out["porcupine"] = "unavailable"
        try:
            from Backend.system_control import get_stats
            s = get_stats()
            out["system_control"] = "ok" if s.get("ok") else "error"
        except Exception:
            out["system_control"] = "error"
        return out

    # Optional: continuous "Hey Boss" hotword listener. Off by default.
    # Prefers Picovoice Porcupine (offline, ~1% CPU). Falls back to the
    # speech_recognition based detector if Porcupine isn't available — that
    # one polls Google Speech every few seconds, so heavier.
    if os.getenv('ENABLE_HOTWORD', 'false').lower() == 'true':
        def _hotword_worker():
            try:
                from Backend import wake_word
                if wake_word.start(eel):
                    print("\n🎤 Wake word ON (Porcupine) — bolo 'Hey Boss' (or trained keyword).\n")
                    return
                # Fall back to the legacy detector
                from hotword_detection import listen_for_hotword
                print("\n🎤 Wake word ON (legacy speech_recognition) — bolo 'Hey Boss' / 'Hey Dude'.\n")
                listen_for_hotword(eel)
            except Exception as e:
                print(f"❌ Hotword detection error: {e}")

        threading.Thread(target=_hotword_worker, daemon=True).start()
    else:
        print("ℹ️  Hotword detection OFF (set ENABLE_HOTWORD=true in .env to enable). "
              "UI me mic dabake bhi baat ho sakti hai.")

    # Proactive system monitor — watches RAM/CPU/Battery and pushes
    # eel.systemAlert(...) to the frontend toast when sustained high.
    if os.getenv('ENABLE_SYSTEM_MONITOR', 'true').lower() == 'true':
        try:
            from Backend.system_control import start_system_monitor
            if start_system_monitor(eel):
                print("📊 System monitor ON — RAM/CPU/Battery watch active.")
        except Exception as e:
            print(f"⚠️  System monitor failed to start: {e}")

    print("=" * 50)
    print("🎙️  Hey Dude Voice Assistant Started — http://localhost:8006")
    print("=" * 50)

    try:
        threading.Thread(target=playassistantsound, daemon=True).start()
    except Exception:
        pass

    _open_browser()
    eel.start('index.html', mode=None, host='localhost', port=8006, block=True)
