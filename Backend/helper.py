import re


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

