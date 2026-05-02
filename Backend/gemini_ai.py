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

# Friendly assistant personality — speaks like a buddy, not a corporate bot.
SYSTEM_INSTRUCTION = (
    "You are Hey Dude, a friendly personal assistant for Mohit. "
    "Talk like a casual, helpful friend — warm, concise, a bit witty. "
    "Default to short answers (1–3 sentences). Only go long if the user "
    "asks for detail or the topic clearly needs it. Use plain language, "
    "skip hedging and corporate filler. If you don't know something, say "
    "so honestly. Today's date and the user's location are real-world "
    "facts you can mention naturally if relevant."
)

_model = None
_chat = None


def _get_chat():
    """Lazy-init the model and chat session. Reused across queries so the
    assistant has memory of the current conversation."""
    global _model, _chat
    if _chat is None:
        _model = genai.GenerativeModel(
            'gemini-2.5-flash',
            system_instruction=SYSTEM_INSTRUCTION,
        )
        _chat = _model.start_chat(history=[])
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
        return "I couldn't find an answer to that."
    except Exception as e:
        print(f"❌ Gemini API Error: {e}")
        return "I'm having trouble reaching the internet right now."


def handle_gemini_query(query):
    """Speak a Gemini answer and surface it in the UI."""
    from Backend.command import speak_text

    try:
        # Quick UI feedback so the user knows something's happening.
        try:
            eel.receiveRecognitionResult("Thinking…")()
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
            speak_text("Check the screen for the full answer.")
        else:
            speak_text(answer)

        return answer

    except Exception as e:
        print(f"❌ Error handling Gemini query: {e}")
        import traceback
        traceback.print_exc()
        error_msg = "Sorry, something went wrong on my end."
        speak_text(error_msg)
        try:
            eel.receiveRecognitionResult(error_msg)()
        except Exception:
            pass
        return error_msg


def search_internet(query):
    return handle_gemini_query(f"Find current information about: {query}")
