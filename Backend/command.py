import pyttsx3
import speech_recognition as sr
import pyaudio
import eel
import threading
import time
import sqlite3
import os
import webbrowser


def speak_text(text):
    """Speak the provided text using pyttsx3. Handles None gracefully."""
    if not text:
        return
    engine = pyttsx3.init('sapi5')
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[0].id)
    engine.setProperty('rate', 174)
    try:
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"Error: {e}")


def execute_command(query):
    """
    Execute command with smart routing priority:
    1. WhatsApp commands
    2. System open commands  
    3. YouTube play commands
    4. Database custom commands
    5. Gemini AI (only if nothing else matches)
    
    Returns: True if command was handled, False otherwise
    """
    command_handled = False
    query_lower = query.lower()
    
    try:
        # 1. WhatsApp commands (highest priority for messaging)
        if "whatsapp" in query_lower or "whats app" in query_lower:
            from Backend.whatsapp import whatsapp_handler
            whatsapp_handler(query)
            command_handled = True
        
        # 2. System open commands
        elif "open" in query_lower:
            from Backend.features import opencommand
            opencommand(query)
            command_handled = True
        
        # 3. YouTube play commands
        elif "play" in query_lower and ("youtube" in query_lower or "on youtube" in query_lower):
            from Backend.features import PlayYoutube
            PlayYoutube(query)
            command_handled = True
        
        # 4. Check database for custom commands
        if not command_handled:
            con = sqlite3.connect("HeyDude.db")
            cursor = con.cursor()
            
            # Check system commands
            cursor.execute("SELECT path FROM sys_commands WHERE name LIKE ?", (f"%{query}%",))
            sys_result = cursor.fetchone()
            
            if sys_result:
                os.startfile(sys_result[0])
                speak_text(f"Opening {query}")
                command_handled = True
            else:
                # Check web commands
                cursor.execute("SELECT url FROM web_commands WHERE name LIKE ?", (f"%{query}%",))
                web_result = cursor.fetchone()
                
                if web_result:
                    webbrowser.open(web_result[0])
                    speak_text(f"Opening {query}")
                    command_handled = True
            
            con.close()
        
        # 5. Only if no command matched, use Gemini AI for general queries
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
    """Listen from microphone and return recognized text (lowercased) or None."""
    r = sr.Recognizer()
    r.pause_threshold = 1
    r.energy_threshold = 4000
    
    with sr.Microphone() as source:
        print("🎤 Listening...")
        r.adjust_for_ambient_noise(source, duration=0.5)
        
        try:
            audio = r.listen(source, timeout=10, phrase_time_limit=8)
        except sr.WaitTimeoutError:
            return None

    try:
        print("🔄 Recognizing...")
        query = r.recognize_google(audio, language='en-in')
        print(f"👤 You said: {query}")
        time.sleep(0.5)
        return query.lower()
    except sr.UnknownValueError:
        return None
    except sr.RequestError as e:
        print(f"❌ Service error: {e}")
        return None
    except Exception as e:
        return None

@eel.expose
def allCommands(message=1):
    """Handle commands from voice or text input.
    message=1 means use voice, otherwise use the text message."""
    
    if message == 1:
        # Voice input
        query = takecommand()
        print(f"Voice command: {query}")
    else:
        # Text input from chat
        query = message.lower() if message else None
        print(f"Text command: {query}")
        # Show the command in UI
        try:
            eel.receiveRecognitionResult(f"You typed: {message}")() 
        except:
            pass
    
    if not query:
        speak_text("No command received")
        return
    
    # Execute command with smart routing
    try:
        execute_command(query)
        
        # Close SiriWave after command
        try:
            eel.closeSiriWave()()
        except:
            pass
            
    except Exception as e:
        print(f"❌ Error processing command: {e}")
        try:
            eel.closeSiriWave()()
        except:
            pass
    
@eel.expose
def start_listen():
    """Start speech recognition in a background thread and send the result to
    the frontend by calling the exposed JS function `receiveRecognitionResult`.

    Returns immediately with a status dict. The actual recognized text will be
    delivered to the frontend when available via `eel.receiveRecognitionResult(text)()`.
    """

    def worker():
        try:
            query = takecommand()
            
            if query:
                # Check if this is the hotword "Hey Dude"
                if "hey dude" in query.lower() or "hai dude" in query.lower() or "hey dud" in query.lower():
                    print("✅ Hotword detected!")
                    try:
                        eel.receiveRecognitionResult("Yes, listening...")()
                    except:
                        pass
                    
                    # Play sound to indicate ready
                    try:
                        from Backend.features import playassistantsound
                        playassistantsound()
                    except:
                        pass
                    
                    # Now listen for the actual command
                    time.sleep(0.5)
                    actual_query = takecommand()
                    
                    if actual_query:
                        query = actual_query
                    else:
                        # No command after hotword
                        speak_text("How can I help?")
                        try:
                            eel.receiveRecognitionResult("How can I help?")()
                            eel.closeSiriWave()()
                        except:
                            pass
                        return
                
                # Now process the command
                try:
                    eel.receiveRecognitionResult(query)()
                except Exception as e:
                    pass
                
                # Execute command with smart routing
                try:
                    execute_command(query)
                    
                    # Command completed - close SiriWave
                    print("✅ Done")
                    try:
                        eel.closeSiriWave()()
                    except:
                        pass
                        
                except Exception as e:
                    print(f"❌ Command error: {e}")
                    # Close SiriWave even on error
                    try:
                        eel.closeSiriWave()()
                    except:
                        pass
            else:
                # No speech recognized
                try:
                    speak_text("Can you repeat?")
                    eel.receiveRecognitionResult("Can you repeat?")()
                    eel.closeSiriWave()()
                except:
                    pass
        except Exception as e:
            print(f"❌ System error")
            # Close SiriWave on any error
            try:
                eel.closeSiriWave()()
            except:
                pass

    t = threading.Thread(target=worker, daemon=True)
    t.start()
    return {"status": "listening_started"}


