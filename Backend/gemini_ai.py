"""Google Gemini AI integration for general queries and internet searches"""
import os
from dotenv import load_dotenv
import google.generativeai as genai
from Backend.command import speak_text
import eel

# Load environment variables from .env file
load_dotenv()

# Configure Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file")

genai.configure(api_key=GEMINI_API_KEY)

# Initialize the model - using gemini-2.5-flash (latest stable model)
model = genai.GenerativeModel('gemini-2.5-flash')

def ask_gemini(query):
    """
    Ask Google Gemini AI a question and return the response.
    This handles general queries, questions, and searches.
    """
    try:
        print(f"🤖 Asking Gemini: {query}")
        
        # Generate response
        response = model.generate_content(query)
        
        if response and response.text:
            answer = response.text.strip()
            print(f"✅ Gemini Response: {answer[:100]}...")
            return answer
        else:
            return "I couldn't find an answer to that."
            
    except Exception as e:
        print(f"❌ Gemini API Error: {e}")
        return "I'm having trouble accessing the information right now."

def handle_gemini_query(query):
    """
    Handle a query using Gemini AI and speak the response.
    This is called for general questions and search queries.
    """
    from Backend.command import speak_text
    import eel
    
    try:
        # Show thinking message
        thinking_msg = "Let me search that for you..."
        print(f"💭 {thinking_msg}")
        try:
            eel.receiveRecognitionResult(thinking_msg)()
        except Exception as e:
            print(f"Error showing thinking message: {e}")
        
        # Speak thinking message
        speak_text(thinking_msg)
        
        # Get response from Gemini
        answer = ask_gemini(query)
        print(f"📝 Got answer from Gemini: {answer[:100]}...")
        
        # Add both question and answer to chat history
        try:
            print("Adding Q&A to chat history...")
            # Add question
            eel.addToChatHistory(query, 'text')()
            # Add answer with a special type
            eel.addToChatHistory(f"🤖 {answer}", 'gemini')()
        except Exception as e:
            print(f"Error adding to chat history: {e}")
        
        # Show response on main page
        try:
            print("Calling showGeminiResponse...")
            eel.showGeminiResponse(answer)()
            print("✓ Response displayed on screen")
        except Exception as e:
            print(f"❌ Error showing response on screen: {e}")
            # Fallback to showing in console
            try:
                eel.receiveRecognitionResult(answer)()
            except:
                pass
        
        # For very long responses, speak a summary
        if len(answer) > 200:
            # Extract first sentence or first 150 chars for speaking
            sentences = answer.split('.')
            first_sentence = sentences[0] + '.' if sentences else answer[:150]
            
            if len(first_sentence) > 150:
                speak_summary = answer[:147] + "..."
            else:
                speak_summary = first_sentence
            
            print(f"🔊 Speaking summary: {speak_summary}")
            speak_text(speak_summary)
            speak_text("Check the screen for the full answer")
        else:
            # Speak the full answer
            print(f"🔊 Speaking full answer")
            speak_text(answer)
        
        return answer
        
    except Exception as e:
        print(f"❌ Error handling Gemini query: {e}")
        import traceback
        traceback.print_exc()
        error_msg = "Sorry, I encountered an error processing your request."
        speak_text(error_msg)
        try:
            eel.receiveRecognitionResult(error_msg)()
        except:
            pass
        return error_msg

def search_internet(query):
    """
    Search the internet using Gemini AI.
    Optimized for search-type queries.
    """
    # Add context to make it a search query
    search_query = f"Search the internet and provide current, accurate information about: {query}"
    return handle_gemini_query(search_query)
