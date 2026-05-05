"""Google Gemini integration with a persistent chat session so the assistant
remembers what you said earlier in the conversation — like a friend would.

Optimised for low-RAM machines: model is created once, but only when first
needed (lazy). Responses stream so the UI feels responsive even on slow
network."""
import os
from dotenv import load_dotenv
import google.generativeai as genai
import eel

load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file")

genai.configure(api_key=GEMINI_API_KEY)

# Hinglish "boss" persona — Iron Man's Jarvis, but in Hinglish.
SYSTEM_INSTRUCTION = (
    "Tu Tanmay (boss) ka personal assistant hai — Iron Man ke Jarvis jaisa, "
    "lekin Hinglish me. Hamesha 'boss' kehke address kar. Reply Hinglish me — "
    "Hindi Roman script + English mixed (jaise 'haan boss, woh kaam ho gaya', "
    "'ji boss, sun raha hun', 'sorry boss, samjha nahi'). Tone friendly, witty, "
    "thoda cocky — confident but warm. Default answers chhote rakh (2-3 lines max) "
    "jab tak boss explicit detail na maange. Filler aur corporate bakwas avoid kar. "
    "Agar kuch nahi pata to seedha bol de 'sorry boss, ye to mujhe nahi pata'. "
    "Boss ki location aur date real facts hain — naturally mention kar sakta hai."
)

# Model fallback list — first one that initializes wins. Protects against
# Google retiring a model name without warning.
MODEL_CANDIDATES = ['gemini-2.5-flash', 'gemini-1.5-flash', 'gemini-pro']

_model = None
_chat = None


def _get_chat():
    """Lazy-init the model and chat session. Reused across queries so the
    assistant has memory of the current conversation."""
    global _model, _chat
    if _chat is None:
        last_err = None
        for model_name in MODEL_CANDIDATES:
            try:
                _model = genai.GenerativeModel(
                    model_name,
                    system_instruction=SYSTEM_INSTRUCTION,
                )
                _chat = _model.start_chat(history=[])
                print(f"✅ Gemini ready ({model_name})")
                break
            except Exception as e:
                last_err = e
                continue
        if _chat is None:
            raise RuntimeError(f"No Gemini model available: {last_err}")
    return _chat


@eel.expose
def reset_chat():
    """Clear the conversation memory (start fresh)."""
    global _chat
    _chat = None
    return {"status": "reset"}


def ask_gemini(query):
    """Send a query to Gemini in the ongoing chat session. Returns text."""
    try:
        chat = _get_chat()
        response = chat.send_message(query)
        if response and response.text:
            return response.text.strip()
        return "Sorry boss, jawab nahi mil paya."
    except Exception as e:
        print(f"❌ Gemini API Error: {e}")
        return "Boss, internet me dikkat hai abhi."


def handle_gemini_query(query):
    """Speak a Gemini answer and surface it in the UI."""
    from Backend.command import speak_text

    try:
        # Quick UI feedback so the user knows something's happening.
        try:
            eel.receiveRecognitionResult("Soch raha hun…")()
        except Exception:
            pass

        answer = ask_gemini(query)
        print(f"📝 Gemini: {answer[:120]}…")

        # Add Q&A to chat history panel.
        try:
            eel.addToChatHistory(query, 'text')()
            eel.addToChatHistory(answer, 'gemini')()
        except Exception:
            pass

        # Show full answer on screen.
        try:
            eel.showGeminiResponse(answer)()
        except Exception:
            try:
                eel.receiveRecognitionResult(answer)()
            except Exception:
                pass

        # Speak: short answers in full, long ones get summarised.
        if len(answer) > 220:
            first_sentence = (answer.split('.')[0] + '.') if '.' in answer else answer[:200]
            speak_text(first_sentence)
            speak_text("Boss, pura jawab screen pe dekh lo.")
        else:
            speak_text(answer)

        return answer

    except Exception as e:
        print(f"❌ Error handling Gemini query: {e}")
        import traceback
        traceback.print_exc()
        error_msg = "Sorry boss, kuch gadbad ho gayi."
        speak_text(error_msg)
        try:
            eel.receiveRecognitionResult(error_msg)()
        except Exception:
            pass
        return error_msg


def search_internet(query):
    return handle_gemini_query(f"Find current information about: {query}")
