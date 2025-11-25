from playsound import playsound
import os
import eel
import re
import pywhatkit as kit
import sqlite3
import webbrowser
from Backend.helper import extract_yt_term

# Define assistant name directly to avoid import issues
ASSISTANT_NAME = "Hey Dude"

# Playing assistant sound function
@eel.expose 
def playassistantsound():
    """Play the startup sound when application starts"""
    try:
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        music_dir = os.path.join(current_dir, "Frontend", "assets( images )", "Audio", "start_sound.mp3")
        
        if os.path.exists(music_dir):
            playsound(music_dir)
    except Exception as e:
        pass

def opencommand(query):
    """Open applications or websites based on voice command using database"""
    from Backend.command import speak_text
    import time
    
    query = query.lower()
    query = query.replace("hey dude", "")
    query = query.replace("open", "")
    app_name = query.strip()
    
    if app_name != "":
        try:
            con = sqlite3.connect("HeyDude.db")
            cursor = con.cursor()
            
            # Wait so user can see their command
            time.sleep(1)
            
            # Try desktop applications first
            cursor.execute('SELECT path FROM sys_commands WHERE name = ?', (app_name,))
            results = cursor.fetchall()
            
            if len(results) != 0:
                response_text = f"Opening {app_name}"
                speak_text(response_text)
                eel.receiveRecognitionResult(response_text)()
                os.startfile(results[0][0])
                
            else:
                # Try web applications
                cursor.execute('SELECT url FROM web_commands WHERE name = ?', (app_name,))
                results = cursor.fetchall()
                
                if len(results) != 0:
                    response_text = f"Opening {app_name}"
                    speak_text(response_text)
                    eel.receiveRecognitionResult(response_text)()
                    webbrowser.open(results[0][0])
                    
                else:
                    # Try generic open
                    response_text = f"Opening {app_name}"
                    speak_text(response_text)
                    eel.receiveRecognitionResult(response_text)()
                    try:
                        os.system('start ' + app_name)
                    except:
                        speak_text("Not found")
                        eel.receiveRecognitionResult("Not found")()
            
            con.close()
            
        except Exception as e:
            speak_text("Something went wrong")
            eel.receiveRecognitionResult("Something went wrong")()
    else:
        speak_text("No application specified")
        eel.receiveRecognitionResult("No application specified")()

def PlayYoutube(query):
    """Play videos on YouTube based on voice command"""
    from Backend.command import speak_text
    import time
    
    # Wait so user can see their command
    time.sleep(1)
    
    search_term = extract_yt_term(query)
    
    if search_term and search_term.strip():
        response_text = f"Yes, playing {search_term} on YouTube"
        speak_text(response_text)
        eel.receiveRecognitionResult(response_text)()
        
        try:
            kit.playonyt(search_term)
        except Exception as e:
            speak_text("Sorry, I couldn't open YouTube")
            eel.receiveRecognitionResult("Sorry, I couldn't open YouTube")()
    else:
        response_text = "Can you repeat your command"
        speak_text(response_text)
        eel.receiveRecognitionResult(response_text)()

def hotword():
    porcupine=None
    paud=None
    audio_stream=None
    try:
       # pre trained keywords    
        porcupine=pvporcupine.create(keywords=["jarvis","Hey Dude"]) 
        paud=pyaudio.PyAudio()
        audio_stream=paud.open(rate=porcupine.sample_rate,channels=1,format=pyaudio.paInt16,input=True,frames_per_buffer=porcupine.frame_length)
        
        # loop for streaming
        while True:
            keyword=audio_stream.read(porcupine.frame_length)
            keyword=struct.unpack_from("h"*porcupine.frame_length,keyword)

            # processing keyword comes from mic 
            keyword_index=porcupine.process(keyword)

            # checking first keyword detetcted for not
            if keyword_index>=0:
                print("hotword detected")

                # pressing shorcut key win+j
                import pyautogui as autogui
                autogui.keyDown("win")
                autogui.press("j")
                time.sleep(2)
                autogui.keyUp("win")
                
    except:
        if porcupine is not None:
            porcupine.delete()
        if audio_stream is not None:
            audio_stream.close()
        if paud is not None:
            paud.terminate()



