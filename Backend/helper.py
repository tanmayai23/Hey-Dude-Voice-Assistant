import re
from Backend.config import ASSISTANT_NAME

def extract_yt_term(command):
    """Extract the search term from YouTube play command"""
    command = command.lower().strip()
    command = command.replace("hey dude", "").strip()
    
    # Define multiple patterns to catch different ways of saying the command
    patterns = [
        r"play\s+(.*?)\s+on\s+youtube",     # "play kinna sona song on youtube"
        r"play\s+(.*?)\s+youtube",          # "play kinna sona song youtube" 
        r"youtube\s+play\s+(.*)",           # "youtube play kinna sona song"
        r"on\s+youtube\s+play\s+(.*)",      # "on youtube play kinna sona song"
        r"play\s+(.*)",                     # "play kinna sona song" (fallback)
    ]
    
    for i, pattern in enumerate(patterns):
        match = re.search(pattern, command, re.IGNORECASE)
        if match:
            search_term = match.group(1).strip()
            search_term = search_term.replace("song", "").strip()
            search_term = search_term.replace("video", "").strip()
            
            if len(search_term) > 1 and not search_term.isspace():
                return search_term
    
    return None

def remove_words(input_strings, words_to_remove):
    # define a regular expressin patern to capture the song name
    words = input_string.split()
    filtered_words = [word for word in words if word.lower() not in words_to_remove]    
    result_string = ' '.join(filtered_words)
    
    return result_string


# Test code - commented out to avoid running on import
# input_string = "make a phone call to papa "
# words_to_remove = [ASSISTANT_NAME, "make", "a", "phone", "call", "to", "send", "message", "whatsapp", ""]
# result = remove_words(input_string, words_to_remove)
# print("Resulting string:", result)
