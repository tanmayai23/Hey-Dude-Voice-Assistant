"""
Alternative Hotword Detection for "Hey Dude"
Uses speech_recognition library - works without API keys
"""

import speech_recognition as sr
import time

def listen_for_hotword(eel_instance):
    """Continuously listen for 'Hey Dude' wake word"""
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 4000  # Adjust for sensitivity
    recognizer.dynamic_energy_threshold = True
    
    print("="*50)
    print("🎤 Hotword Detection Active - Waiting for 'Hey Dude'")
    print("="*50)
    
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=2)
        
        while True:
            try:
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=3)
                
                try:
                    # Recognize speech
                    text = recognizer.recognize_google(audio, language='en-in')
                    text_lower = text.lower()
                    
                    # Check if "hey dude" is in the spoken text
                    if "hey dude" in text_lower or "hai dude" in text_lower or "hey dud" in text_lower:
                        print("\n✅ Hotword detected: 'Hey Dude'")
                        
                        # Trigger the mic activation via Eel function call
                        try:
                            if eel_instance:
                                eel_instance.activateMicFromHotword()
                                print("✅ Activated mic through Eel")
                        except Exception as e:
                            print(f"⚠️  Could not activate mic via Eel: {e}")

                        # Debounce before listening again
                        time.sleep(2)
                    
                except sr.UnknownValueError:
                    # Speech not clear enough - silent fail
                    pass
                    
                except sr.RequestError as e:
                    print(f"❌ Service error: {e}")
                    
            except sr.WaitTimeoutError:
                # No speech detected - continue silently
                continue
                
            except KeyboardInterrupt:
                print("\n⛔ Stopping hotword detection...")
                break
                
            except Exception as e:
                print(f"❌ Error: {e}")
                continue

def main():
    """Main function to start hotword detection"""
    try:
        listen_for_hotword(None)
    except KeyboardInterrupt:
        print("\n✅ Hotword detection stopped")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")

if __name__ == "__main__":
    main()
