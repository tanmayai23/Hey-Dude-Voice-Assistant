import eel
import threading
import time
import sqlite3
import os
import webbrowser

# pyttsx3 engine is cached at module level — initialising SAPI5 takes ~250ms
# and adds noticeable lag on every reply. We init lazily on first speak().
_tts_engine = None
_tts_lock = threading.Lock()

# TTS_PROVIDER=kokoro (default) routes through cloud Kokoro-82M and falls
# back to pyttsx3 on any failure. Set TTS_PROVIDER=pyttsx3 to force the
# local SAPI5 voice (e.g. when offline or the API key isn't set).
_TTS_PROVIDER = os.getenv('TTS_PROVIDER', 'kokoro').strip().lower() or 'kokoro'

# ASR_PROVIDER=groq (default) routes mic audio through Groq's Whisper
# (free tier covers ~8hrs/day). Falls back to recognize_google on failure
# so offline use or missing keys still work.
_ASR_PROVIDER = os.getenv('ASR_PROVIDER', 'groq').strip().lower() or 'groq'


def _get_tts_engine():
    global _tts_engine
    if _tts_engine is not None:
        return _tts_engine
    import pyttsx3
    engine = pyttsx3.init('sapi5')
    voices = engine.getProperty('voices')
    if voices:
        # Prefer an Indian / Hindi voice if Windows has one installed —
        # falls back to the default voice otherwise. Better fit for Hinglish.
        chosen = voices[0].id
        for v in voices:
            name = (getattr(v, 'name', '') or '').lower()
            langs = ' '.join(str(x) for x in (getattr(v, 'languages', []) or [])).lower()
            if any(k in name for k in ('ravi', 'hindi', 'india', 'kalpana', 'hemant')) \
               or 'hi-in' in langs or 'en-in' in langs:
                chosen = v.id
                break
        engine.setProperty('voice', chosen)
    engine.setProperty('rate', 174)
    _tts_engine = engine
    return engine


def _speak_pyttsx3(text):
    global _tts_engine
    try:
        engine = _get_tts_engine()
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"TTS error (pyttsx3): {e}")
        # Reset engine so the next call rebuilds it cleanly.
        _tts_engine = None


def _speak_kokoro(text) -> bool:
    """Synthesize via DeepInfra Kokoro and play the WAV. Returns True on
    success, False if the caller should fall back to pyttsx3."""
    try:
        from Backend import tts_kokoro
    except Exception as e:
        print(f"Kokoro import failed: {e}")
        return False
    if not tts_kokoro.is_configured():
        return False
    try:
        wav_path = tts_kokoro.synthesize_to_file(text)
    except Exception as e:
        print(f"Kokoro synth failed, falling back to pyttsx3: {e}")
        return False
    try:
        from playsound import playsound
        playsound(wav_path, block=True)
        return True
    except Exception as e:
        print(f"Kokoro playback failed, falling back to pyttsx3: {e}")
        return False


def speak_text(text):
    """Speak text. Tries cloud Kokoro first (warm voice), falls back to
    pyttsx3 (Windows SAPI5) on any failure — so offline mode still works."""
    if not text:
        return
    with _tts_lock:
        if _TTS_PROVIDER == 'kokoro' and _speak_kokoro(text):
            return
        _speak_pyttsx3(text)


def execute_command(query):
    """Smart routing: WhatsApp > open > YouTube > custom DB > Gemini fallback."""
    command_handled = False
    query_lower = query.lower()

    try:
        if "whatsapp" in query_lower or "whats app" in query_lower:
            from Backend.whatsapp import whatsapp_handler
            whatsapp_handler(query)
            command_handled = True

        elif "open" in query_lower:
            from Backend.features import opencommand
            opencommand(query)
            command_handled = True

        elif "play" in query_lower and ("youtube" in query_lower or "on youtube" in query_lower):
            from Backend.features import PlayYoutube
            PlayYoutube(query)
            command_handled = True

        elif any(k in query_lower for k in ("weather", "mausam", "temperature")):
            from Backend.weather import get_weather
            summary = get_weather(query)
            speak_text(summary)
            try:
                eel.showGeminiResponse(summary)()
            except Exception:
                pass
            command_handled = True

        elif any(k in query_lower for k in ("ram check", "ram kitna", "ram kitni", "memory kitni", "memory check")):
            from Backend.system_control import get_stats, top_hogs
            s = get_stats(); h = top_hogs(5)
            if s.get('ok'):
                msg = (f"Boss, RAM {s['ram']}% use ho rahi hai "
                       f"({s['ram_used_gb']} GB / {s['ram_total_gb']} GB). CPU {s['cpu']}%.")
                speak_text(msg)
                detail = msg + "\n\nTop memory hogs:\n" + "\n".join(
                    f"• {p['name']} — {p['rss_mb']} MB" for p in h
                )
                try: eel.showGeminiResponse(detail)()
                except Exception: pass
            else:
                speak_text("Boss, system stats nahi mil paye.")
            command_handled = True

        elif any(k in query_lower for k in ("saaf kar", "clean cache", "cache saaf", "cleanup")):
            from Backend.system_control import cleanup_caches
            speak_text("Saaf kar raha hun boss, ek minute.")
            r = cleanup_caches(confirm=True)
            if r.get('ok'):
                speak_text(f"Saaf ho gaya boss, {r.get('freed_mb', 0)} MB free kar diya.")
            else:
                speak_text("Cleanup me thodi dikkat aayi boss.")
            command_handled = True

        elif "screenshot" in query_lower:
            from Backend.system_control import take_screenshot
            r = take_screenshot()
            if r.get('ok'):
                speak_text(f"Screenshot le liya boss, {os.path.basename(r['path'])} me save ho gaya.")
                try: eel.showGeminiResponse(f"Screenshot saved:\n{r['path']}")()
                except Exception: pass
            else:
                speak_text("Screenshot fail ho gaya boss.")
            command_handled = True

        elif "volume" in query_lower:
            import re
            from Backend.system_control import set_volume, mute_volume, get_stats
            if "mute" in query_lower:
                mute_volume(); speak_text("Mute kar diya boss.")
            elif "unmute" in query_lower:
                mute_volume(False); speak_text("Unmute kar diya boss.")
            elif "up" in query_lower or "badha" in query_lower:
                cur = get_stats().get('volume', 50)
                set_volume(min(100, cur + 10)); speak_text("Volume badha diya boss.")
            elif "down" in query_lower or "kam" in query_lower:
                cur = get_stats().get('volume', 50)
                set_volume(max(0, cur - 10)); speak_text("Volume kam kar diya boss.")
            else:
                m = re.search(r'(\d+)', query_lower)
                if m:
                    set_volume(int(m.group(1)))
                    speak_text(f"Volume {m.group(1)} pe set kar diya boss.")
                else:
                    speak_text("Volume kitna karu boss? Number bolo.")
            command_handled = True

        elif "brightness" in query_lower:
            import re
            from Backend.system_control import set_brightness
            m = re.search(r'(\d+)', query_lower)
            if m:
                r = set_brightness(int(m.group(1)))
                if r.get('ok'):
                    speak_text(f"Brightness {m.group(1)} pe kar di boss.")
                else:
                    speak_text("Brightness change nahi ho payi boss.")
            else:
                speak_text("Brightness kitni karu boss? Number bolo.")
            command_handled = True

        elif "battery" in query_lower:
            from Backend.system_control import get_stats
            s = get_stats()
            if s.get('battery') is not None:
                plug = "charging pe hai" if s.get('plugged') else "battery pe chal raha hai"
                speak_text(f"Boss, battery {s['battery']}% hai aur {plug}.")
            else:
                speak_text("Boss, ye desktop hai shayad — battery info nahi mili.")
            command_handled = True

        elif "lock" in query_lower and ("screen" in query_lower or "kar de" in query_lower or "kardo" in query_lower or "kar do" in query_lower):
            from Backend.system_control import lock_screen
            speak_text("Lock kar raha hun boss.")
            time.sleep(0.5)
            lock_screen()
            command_handled = True

        elif "download" in query_lower:
            import re
            from Backend.file_ops import download_file
            m = re.search(r'(https?://\S+)', query)
            if m:
                speak_text("Download shuru kar raha hun boss.")
                r = download_file(m.group(1))
                if r.get('ok'):
                    speak_text(f"Boss, {r.get('size_mb', 0)} MB ki file download ho gayi.")
                    try: eel.showGeminiResponse(f"Saved to:\n{r['path']}")()
                    except Exception: pass
                else:
                    speak_text(f"Download fail ho gaya boss — {r.get('error', 'unknown error')}.")
            else:
                speak_text("Boss, URL bolo download karne ke liye.")
            command_handled = True

        elif "notepad" in query_lower and ("likho" in query_lower or "write" in query_lower):
            import re
            from Backend.file_ops import write_file_to_app
            m = re.search(r'(?:likho|write)\s+(.+)$', query, re.IGNORECASE)
            if m:
                content = m.group(1).strip()
                speak_text("Notepad me likh raha hun boss.")
                r = write_file_to_app(content, app='notepad')
                if r.get('ok'):
                    speak_text("Notepad me likh diya boss.")
                else:
                    speak_text("Notepad me likhne me dikkat aayi boss.")
            else:
                speak_text("Boss, kya likhna hai bolo.")
            command_handled = True

        elif query_lower.startswith("dhundo ") or query_lower.startswith("find "):
            from Backend.file_ops import find_file
            name = query_lower.replace("dhundo", "").replace("find", "").strip()
            if name:
                speak_text(f"Boss, {name} dhund raha hun.")
                r = find_file(name)
                if r.get('ok'):
                    n = len(r.get('paths', []))
                    speak_text(f"Boss, {n} file mil gayi." if n else "Boss, kuch nahi mila.")
                    if n:
                        try:
                            eel.showGeminiResponse(
                                f"Found {n} file(s):\n\n" + "\n".join(r['paths'][:20])
                            )()
                        except Exception: pass
                else:
                    speak_text("Search fail ho gaya boss.")
            else:
                speak_text("Boss, file ka naam bolo.")
            command_handled = True

        if not command_handled:
            con = sqlite3.connect("HeyDude.db")
            cursor = con.cursor()

            cursor.execute("SELECT path FROM sys_commands WHERE name LIKE ?", (f"%{query}%",))
            sys_result = cursor.fetchone()

            if sys_result:
                os.startfile(sys_result[0])
                speak_text(f"Boss, {query} khol raha hun")
                command_handled = True
            else:
                cursor.execute("SELECT url FROM web_commands WHERE name LIKE ?", (f"%{query}%",))
                web_result = cursor.fetchone()
                if web_result:
                    webbrowser.open(web_result[0])
                    speak_text(f"Boss, {query} khol raha hun")
                    command_handled = True

            con.close()

        if not command_handled:
            print("ℹ️  No command matched - Using Gemini AI for general query")
            from Backend.gemini_ai import handle_gemini_query
            handle_gemini_query(query)
            command_handled = True

    except Exception as e:
        print(f"❌ Error executing command: {e}")

    return command_handled


@eel.expose
def takecommand():
    """Listen from mic and return recognized text (lowercased) or None.

    Tuning notes:
    - dynamic_energy_threshold lets the recognizer auto-calibrate to your
      ambient noise level — far more reliable than a fixed value.
    - energy_threshold seeded at 300 (the library default), not 4000, so
      normal-volume speech gets picked up.
    - pause_threshold 0.6s feels conversational without cutting words.
    - phrase_time_limit 12s caps long rambling queries.
    """
    import speech_recognition as sr

    r = sr.Recognizer()
    r.dynamic_energy_threshold = True
    r.energy_threshold = 300
    # Pause threshold is generous so the user can take breaths without
    # being cut off mid-sentence.
    r.pause_threshold = 1.2
    r.phrase_threshold = 0.2
    r.non_speaking_duration = 0.6

    try:
        with sr.Microphone() as source:
            print("🎤 Listening...")
            r.adjust_for_ambient_noise(source, duration=0.4)
            try:
                # Long phrase budget (30s) so Tanmay can finish complete
                # thoughts without the recognizer cutting him off.
                audio = r.listen(source, timeout=10, phrase_time_limit=30)
            except sr.WaitTimeoutError:
                print("⌛ No speech heard within timeout.")
                return None
    except Exception as e:
        print(f"❌ Microphone error: {e}")
        return None

    print("🔄 Recognizing...")

    if _ASR_PROVIDER == 'groq':
        try:
            from Backend import asr_groq
            if asr_groq.is_configured():
                query = asr_groq.transcribe(audio)
                print(f"👤 You said (Groq): {query}")
                return query.lower()
        except Exception as e:
            print(f"⚠️  Groq ASR failed, falling back to Google: {e}")

    try:
        query = r.recognize_google(audio, language='en-in')
        print(f"👤 You said: {query}")
        return query.lower()
    except sr.UnknownValueError:
        print("🤷 Speech unintelligible.")
        return None
    except sr.RequestError as e:
        print(f"❌ Service error: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected STT error: {e}")
        return None


@eel.expose
def allCommands(message=1):
    """Handle commands from voice or text input.
    message=1 means use voice, otherwise use the text message."""
    if message == 1:
        query = takecommand()
        print(f"Voice command: {query}")
    else:
        query = message.lower() if message else None
        print(f"Text command: {query}")
        try:
            eel.receiveRecognitionResult(f"You typed: {message}")()
        except Exception:
            pass

    if not query:
        speak_text("Boss, kuch suna nahi maine.")
        return

    try:
        execute_command(query)
        try:
            eel.closeSiriWave()()
        except Exception:
            pass
    except Exception as e:
        print(f"❌ Error processing command: {e}")
        try:
            eel.closeSiriWave()()
        except Exception:
            pass


@eel.expose
def start_listen():
    """Run speech recognition in a background thread; deliver result to the
    frontend via eel.receiveRecognitionResult."""

    def worker():
        try:
            query = takecommand()

            if query:
                wake_words = (
                    "hey boss", "hai boss",
                    "hey dude", "hai dude", "hey dud",
                )
                if any(w in query.lower() for w in wake_words):
                    print("✅ Hotword detected!")
                    try:
                        eel.receiveRecognitionResult("Ji boss, sun raha hun...")()
                    except Exception:
                        pass

                    try:
                        from Backend.features import playassistantsound
                        playassistantsound()
                    except Exception:
                        pass

                    time.sleep(0.5)
                    actual_query = takecommand()

                    if actual_query:
                        query = actual_query
                    else:
                        speak_text("Bolo boss, kaise madad karun?")
                        try:
                            eel.receiveRecognitionResult("Bolo boss, kaise madad karun?")()
                            eel.closeSiriWave()()
                        except Exception:
                            pass
                        return

                try:
                    eel.receiveRecognitionResult(query)()
                except Exception:
                    pass

                try:
                    execute_command(query)
                    print("✅ Done")
                    try:
                        eel.closeSiriWave()()
                    except Exception:
                        pass
                except Exception as e:
                    print(f"❌ Command error: {e}")
                    try:
                        eel.closeSiriWave()()
                    except Exception:
                        pass
            else:
                try:
                    speak_text("Sorry boss, samjha nahi — phir se bolo?")
                    eel.receiveRecognitionResult("Sorry boss, samjha nahi — phir se bolo?")()
                    eel.closeSiriWave()()
                except Exception:
                    pass
        except Exception:
            print("❌ System error")
            try:
                eel.closeSiriWave()()
            except Exception:
                pass

    t = threading.Thread(target=worker, daemon=True)
    t.start()
    return {"status": "listening_started"}
