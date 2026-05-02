import eel
import threading
import time
import sqlite3
import os
import webbrowser


def speak_text(text):
    """Speak text using pyttsx3. Engine is created per-call and released so we
    don't hold SAPI5 COM resources at idle."""
    if not text:
        return
    try:
        import pyttsx3
        engine = pyttsx3.init('sapi5')
        voices = engine.getProperty('voices')
        if voices:
            engine.setProperty('voice', voices[0].id)
        engine.setProperty('rate', 174)
        engine.say(text)
        engine.runAndWait()
        try:
            engine.stop()
            del engine
        except Exception:
            pass
    except Exception as e:
        print(f"TTS error: {e}")


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

        if not command_handled:
            con = sqlite3.connect("HeyDude.db")
            cursor = con.cursor()

            cursor.execute("SELECT path FROM sys_commands WHERE name LIKE ?", (f"%{query}%",))
            sys_result = cursor.fetchone()

            if sys_result:
                os.startfile(sys_result[0])
                speak_text(f"Opening {query}")
                command_handled = True
            else:
                cursor.execute("SELECT url FROM web_commands WHERE name LIKE ?", (f"%{query}%",))
                web_result = cursor.fetchone()
                if web_result:
                    webbrowser.open(web_result[0])
                    speak_text(f"Opening {query}")
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

    try:
        print("🔄 Recognizing...")
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
        speak_text("No command received")
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
                if any(w in query.lower() for w in ("hey dude", "hai dude", "hey dud")):
                    print("✅ Hotword detected!")
                    try:
                        eel.receiveRecognitionResult("Yes, listening...")()
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
                        speak_text("How can I help?")
                        try:
                            eel.receiveRecognitionResult("How can I help?")()
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
                    speak_text("Can you repeat?")
                    eel.receiveRecognitionResult("Can you repeat?")()
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
