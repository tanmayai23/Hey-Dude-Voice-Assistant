import os
import eel
import sqlite3
import webbrowser
from Backend.helper import extract_yt_term

ASSISTANT_NAME = "Hey Dude"


@eel.expose
def playassistantsound():
    """Play startup sound. playsound is imported lazily to keep idle RAM low."""
    try:
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        music_dir = os.path.join(current_dir, "Frontend", "assets( images )", "Audio", "start_sound.mp3")

        if os.path.exists(music_dir):
            from playsound import playsound
            playsound(music_dir)
    except Exception:
        pass


def opencommand(query):
    """Open applications or websites based on voice command using database."""
    from Backend.command import speak_text
    import time

    query = query.lower()
    query = query.replace("hey dude", "")
    query = query.replace("open", "")
    app_name = query.strip()

    if not app_name:
        speak_text("No application specified")
        eel.receiveRecognitionResult("No application specified")()
        return

    try:
        con = sqlite3.connect("HeyDude.db")
        cursor = con.cursor()
        time.sleep(1)

        cursor.execute('SELECT path FROM sys_commands WHERE name = ?', (app_name,))
        results = cursor.fetchall()

        if results:
            response_text = f"Opening {app_name}"
            speak_text(response_text)
            eel.receiveRecognitionResult(response_text)()
            os.startfile(results[0][0])
        else:
            cursor.execute('SELECT url FROM web_commands WHERE name = ?', (app_name,))
            results = cursor.fetchall()

            if results:
                response_text = f"Opening {app_name}"
                speak_text(response_text)
                eel.receiveRecognitionResult(response_text)()
                webbrowser.open(results[0][0])
            else:
                response_text = f"Opening {app_name}"
                speak_text(response_text)
                eel.receiveRecognitionResult(response_text)()
                try:
                    os.system('start ' + app_name)
                except Exception:
                    speak_text("Not found")
                    eel.receiveRecognitionResult("Not found")()

        con.close()

    except Exception:
        speak_text("Something went wrong")
        eel.receiveRecognitionResult("Something went wrong")()


def PlayYoutube(query):
    """Play videos on YouTube. pywhatkit is heavy (PIL/requests) — import lazily."""
    from Backend.command import speak_text
    import time

    time.sleep(1)
    search_term = extract_yt_term(query)

    if not (search_term and search_term.strip()):
        response_text = "Can you repeat your command"
        speak_text(response_text)
        eel.receiveRecognitionResult(response_text)()
        return

    response_text = f"Yes, playing {search_term} on YouTube"
    speak_text(response_text)
    eel.receiveRecognitionResult(response_text)()

    try:
        import pywhatkit as kit
        kit.playonyt(search_term)
    except Exception:
        speak_text("Sorry, I couldn't open YouTube")
        eel.receiveRecognitionResult("Sorry, I couldn't open YouTube")()
