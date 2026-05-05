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
    for wake in ("hey boss", "hai boss", "hey dude", "hai dude"):
        query = query.replace(wake, "")
    query = query.replace("open", "")
    app_name = query.strip()

    if not app_name:
        speak_text("Boss, kya kholna hai bataiye")
        eel.receiveRecognitionResult("Boss, kya kholna hai bataiye")()
        return

    try:
        con = sqlite3.connect("HeyDude.db")
        cursor = con.cursor()
        time.sleep(1)

        cursor.execute('SELECT path FROM sys_commands WHERE name = ?', (app_name,))
        results = cursor.fetchall()

        if results:
            response_text = f"Boss, {app_name} khol raha hun"
            speak_text(response_text)
            eel.receiveRecognitionResult(response_text)()
            os.startfile(results[0][0])
        else:
            cursor.execute('SELECT url FROM web_commands WHERE name = ?', (app_name,))
            results = cursor.fetchall()

            if results:
                response_text = f"Boss, {app_name} khol raha hun"
                speak_text(response_text)
                eel.receiveRecognitionResult(response_text)()
                webbrowser.open(results[0][0])
            else:
                response_text = f"Boss, {app_name} kholne ki koshish kar raha hun"
                speak_text(response_text)
                eel.receiveRecognitionResult(response_text)()
                try:
                    os.system('start ' + app_name)
                except Exception:
                    speak_text("Sorry boss, ye mil nahi raha")
                    eel.receiveRecognitionResult("Sorry boss, ye mil nahi raha")()

        con.close()

    except Exception:
        speak_text("Sorry boss, kuch gadbad ho gayi")
        eel.receiveRecognitionResult("Sorry boss, kuch gadbad ho gayi")()


def PlayYoutube(query):
    """Play videos on YouTube. pywhatkit is heavy (PIL/requests) — import lazily."""
    from Backend.command import speak_text
    import time

    time.sleep(1)
    search_term = extract_yt_term(query)

    if not (search_term and search_term.strip()):
        response_text = "Sorry boss, samjha nahi — phir se bolo"
        speak_text(response_text)
        eel.receiveRecognitionResult(response_text)()
        return

    response_text = f"Ji boss, YouTube pe {search_term} chala raha hun"
    speak_text(response_text)
    eel.receiveRecognitionResult(response_text)()

    try:
        import pywhatkit as kit
        kit.playonyt(search_term)
    except Exception:
        speak_text("Sorry boss, YouTube nahi khul paya")
        eel.receiveRecognitionResult("Sorry boss, YouTube nahi khul paya")()
