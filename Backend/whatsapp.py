"""
WhatsApp Automation Module
Handles sending messages, voice calls, and video calls via WhatsApp Desktop app
"""

import sqlite3
import subprocess
import time
import pyautogui
import os
import pyperclip
from urllib.parse import quote

def get_contact_number(contact_name):
    """Get mobile number from contacts database by name (partial match)
    Returns: (phone_number, full_name) or None if not found
    """
    try:
        con = sqlite3.connect("HeyDude.db")
        cursor = con.cursor()
        
        # Search for contact (case-insensitive, partial match)
        cursor.execute("SELECT name, mobile_no FROM contacts WHERE LOWER(name) LIKE LOWER(?)", (f'%{contact_name}%',))
        result = cursor.fetchone()
        con.close()
        
        if result:
            return (result[1], result[0])  # Return (phone_number, full_name)
        return None
    except Exception as e:
        return None

def get_all_matching_contacts(contact_name):
    """Get all contacts matching the name"""
    try:
        con = sqlite3.connect("HeyDude.db")
        cursor = con.cursor()
        
        # Search for all matching contacts
        cursor.execute("SELECT name, mobile_no FROM contacts WHERE LOWER(name) LIKE LOWER(?) LIMIT 10", (f'%{contact_name}%',))
        results = cursor.fetchall()
        con.close()
        
        return results  # Returns list of (name, phone) tuples
    except Exception as e:
        return []

def open_whatsapp_desktop():
    """Open WhatsApp Desktop application"""
    try:
        # Try to open WhatsApp Desktop
        whatsapp_paths = [
            os.path.join(os.environ.get('LOCALAPPDATA', ''), 'WhatsApp', 'WhatsApp.exe'),
            os.path.join(os.environ.get('PROGRAMFILES', ''), 'WhatsApp', 'WhatsApp.exe'),
            'C:\\Users\\' + os.environ.get('USERNAME', '') + '\\AppData\\Local\\WhatsApp\\WhatsApp.exe',
        ]
        
        # Try each path
        for path in whatsapp_paths:
            if os.path.exists(path):
                subprocess.Popen([path])
                time.sleep(3)
                return True
        
        # Try using protocol
        try:
            os.startfile('whatsapp://')
            time.sleep(3)
            return True
        except:
            pass
        
        return False
        
    except Exception as e:
        return False

def search_and_open_contact(contact_name):
    """Search for contact in WhatsApp and open chat"""
    try:
        # Wait for WhatsApp to be ready
        time.sleep(2)
        
        # Click on search bar (Ctrl+F)
        pyautogui.hotkey('ctrl', 'f')
        time.sleep(0.5)
        
        # Clear any existing search
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.2)
        
        # Type contact name
        pyautogui.write(contact_name, interval=0.1)
        time.sleep(2)  # Wait for search results
        
        # Press Down arrow to select first result
        pyautogui.press('down')
        time.sleep(0.3)
        
        # Press Enter to open the chat
        pyautogui.press('enter')
        time.sleep(1.5)
        
        # Press Escape to close search and focus on chat
        pyautogui.press('escape')
        time.sleep(0.5)
        
        # Press Tab to move to message input field
        pyautogui.press('tab')
        time.sleep(0.3)
        
        return True
    except Exception as e:
        return False

def send_whatsapp_message(contact_name, message):
    """Send WhatsApp message to a contact via Desktop app"""
    try:
        # Open WhatsApp Desktop
        if not open_whatsapp_desktop():
            return False, "WhatsApp Desktop not found"
        
        # Search and open contact
        if not search_and_open_contact(contact_name):
            return False, f"Could not find contact: {contact_name}"
        
        # Now we should be in the message input field
        time.sleep(0.5)
        
        # Use clipboard to paste message (more reliable)
        pyperclip.copy(message)
        time.sleep(0.2)
        
        # Paste the message (Ctrl+V)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.5)
        
        # Press Enter to send
        pyautogui.press('enter')
        time.sleep(1)
        
        return True, f"Message sent to {contact_name}"
        
    except Exception as e:
        return False, f"Error sending message: {str(e)}"

def make_whatsapp_call(contact_name, call_type="voice"):
    """Make WhatsApp voice or video call via Desktop app"""
    try:
        # Open WhatsApp Desktop
        if not open_whatsapp_desktop():
            return False, "WhatsApp Desktop not found"
        
        # Search and open contact
        if not search_and_open_contact(contact_name):
            return False, f"Could not find contact: {contact_name}"
        
        # After opening chat, press Escape to ensure proper focus
        pyautogui.press('escape')
        time.sleep(0.5)
        
        # Make the call using keyboard shortcuts
        if call_type == "video":
            # Ctrl+Shift+V for video call
            pyautogui.hotkey('ctrl', 'shift', 'v')
            return True, f"Video call started with {contact_name}"
        else:
            # Ctrl+Shift+C for voice call
            pyautogui.hotkey('ctrl', 'shift', 'c')
            return True, f"Voice call started with {contact_name}"
            
    except Exception as e:
        return False, f"Error making call: {str(e)}"

def whatsapp_handler(query, from_command_py=None):
    """Main handler for WhatsApp commands
    
    This function processes voice commands and coordinates the conversation flow
    """
    from Backend.command import speak_text, takecommand
    import eel
    
    query_lower = query.lower()
    
    # Check if it's a WhatsApp command
    if "whatsapp" in query_lower or "whats app" in query_lower:
        
        # Send message flow
        if "send message" in query_lower or "message" in query_lower:
            # Ask for contact name
            max_retries = 2
            contact_name = None
            selected_contact = None
            in_number_selection = False
            current_matches = []
            
            for attempt in range(max_retries):
                if in_number_selection:
                    # We're asking for a number from the list
                    speak_text("Say the number")
                    eel.receiveRecognitionResult("Which number?")() 
                elif attempt == 0:
                    speak_text("To whom should I send the message?")
                    eel.receiveRecognitionResult("To whom?")() 
                else:
                    speak_text("Say the contact name again")
                    eel.receiveRecognitionResult("Try again")()
                
                # Get contact name or number
                contact_response = takecommand()
                
                if contact_response:
                    # If we're in number selection mode
                    if in_number_selection:
                        import re
                        numbers = re.findall(r'\d+', contact_response)
                        if numbers:
                            choice_num = int(numbers[0])
                            if 1 <= choice_num <= len(current_matches):
                                selected_contact = current_matches[choice_num - 1]
                                break
                        
                        # If no number, try name matching
                        for contact in current_matches:
                            if contact_response.lower() in contact[0].lower():
                                selected_contact = contact
                                break
                        if selected_contact:
                            break
                        continue
                    
                    # First time or retry - get contact name
                    contact_name = contact_response.strip()
                    
                    # Get all matching contacts
                    matching_contacts = get_all_matching_contacts(contact_name)
                    
                    if len(matching_contacts) == 0:
                        speak_text(f"Sorry, I couldn't find {contact_name}")
                        eel.receiveRecognitionResult(f"Not found: {contact_name}")()
                        contact_name = None
                    elif len(matching_contacts) == 1:
                        # Only one match, use it
                        selected_contact = matching_contacts[0]
                        break
                    else:
                        # Multiple matches - show numbered options
                        current_matches = matching_contacts
                        in_number_selection = True
                        
                        options_text = ""
                        for i, contact in enumerate(matching_contacts[:5], 1):
                            options_text += f"{i}. {contact[0]}, "
                        options_text = options_text.rstrip(", ")
                        
                        speak_text(f"Multiple contacts found. Say the number: {options_text}")
                        eel.receiveRecognitionResult(f"Say number: {options_text}")()
                        
                        # Get number choice
                        choice_response = takecommand()
                        if choice_response:
                            # Try to extract number from response
                            import re
                            numbers = re.findall(r'\d+', choice_response)
                            if numbers:
                                choice_num = int(numbers[0])
                                if 1 <= choice_num <= len(matching_contacts):
                                    selected_contact = matching_contacts[choice_num - 1]
                                    break
                            
                            # If no number, try name matching
                            for contact in matching_contacts:
                                if choice_response.lower() in contact[0].lower():
                                    selected_contact = contact
                                    break
                            if selected_contact:
                                break
            
            if not selected_contact:
                speak_text("Couldn't find the contact")
                eel.receiveRecognitionResult("❌ Contact not found")()
                return
            
            final_contact_name = selected_contact[0]
            
            # Ask for message content
            message = None
            
            for attempt in range(2):
                if attempt == 0:
                    speak_text(f"What message for {final_contact_name}?")
                    eel.receiveRecognitionResult(f"Message for {final_contact_name}?")()
                else:
                    speak_text("Say your message again")
                    eel.receiveRecognitionResult("Say message again")()
                
                # Get message
                message_response = takecommand()
                
                if message_response:
                    message = message_response.strip()
                    break
            
            if not message:
                speak_text("No message received. Cancelling.")
                eel.receiveRecognitionResult("❌ Cancelled")()
                return
            
            # Send the message
            speak_text(f"Sending to {final_contact_name}")
            eel.receiveRecognitionResult(f"Sending to {final_contact_name}")()
            
            success, result_msg = send_whatsapp_message(final_contact_name, message)
            
            if success:
                speak_text("Message sent")
                eel.receiveRecognitionResult(f"✅ Sent to {final_contact_name}")()
            else:
                speak_text("Failed to send")
                eel.receiveRecognitionResult(f"❌ {result_msg}")()
        
        # Voice call flow
        elif "voice call" in query_lower or "call" in query_lower:
            # Ask for contact name
            contact_name = None
            selected_contact = None
            in_number_selection = False
            current_matches = []
            
            for attempt in range(2):
                if in_number_selection:
                    speak_text("Say the number")
                    eel.receiveRecognitionResult("Which number?")()
                elif attempt == 0:
                    speak_text("Who do you want to call?")
                    eel.receiveRecognitionResult("Call who?")()
                else:
                    speak_text("Say the name again")
                    eel.receiveRecognitionResult("Try again")()
                
                # Get contact name or number
                contact_response = takecommand()
                
                if contact_response:
                    # If we're in number selection mode
                    if in_number_selection:
                        import re
                        numbers = re.findall(r'\d+', contact_response)
                        if numbers:
                            choice_num = int(numbers[0])
                            if 1 <= choice_num <= len(current_matches):
                                selected_contact = current_matches[choice_num - 1]
                                break
                        
                        # If no number, try name matching
                        for contact in current_matches:
                            if contact_response.lower() in contact[0].lower():
                                selected_contact = contact
                                break
                        if selected_contact:
                            break
                        continue
                    
                    # First time or retry - get contact name
                    contact_name = contact_response.strip()
                    
                    # Get all matching contacts
                    matching_contacts = get_all_matching_contacts(contact_name)
                    
                    if len(matching_contacts) == 0:
                        speak_text(f"Contact {contact_name} not found")
                        contact_name = None
                    elif len(matching_contacts) == 1:
                        selected_contact = matching_contacts[0]
                        break
                    else:
                        # Multiple matches - show numbered options
                        current_matches = matching_contacts
                        in_number_selection = True
                        
                        options_text = ""
                        for i, contact in enumerate(matching_contacts[:5], 1):
                            options_text += f"{i}. {contact[0]}, "
                        options_text = options_text.rstrip(", ")
                        
                        speak_text(f"Multiple contacts found. Say the number: {options_text}")
                        eel.receiveRecognitionResult(f"Say number: {options_text}")()
                        
                        # Get number choice
                        choice_response = takecommand()
                        if choice_response:
                            # Try to extract number from response
                            import re
                            numbers = re.findall(r'\d+', choice_response)
                            if numbers:
                                choice_num = int(numbers[0])
                                if 1 <= choice_num <= len(matching_contacts):
                                    selected_contact = matching_contacts[choice_num - 1]
                                    break
                            
                            # If no number, try name matching
                            for contact in matching_contacts:
                                if choice_response.lower() in contact[0].lower():
                                    selected_contact = contact
                                    break
                            if selected_contact:
                                break
            
            if not selected_contact:
                speak_text("Couldn't find contact. Cancelling.")
                eel.receiveRecognitionResult("❌ Cancelled")()
                return
            
            final_contact_name = selected_contact[0]
            
            final_contact_name = selected_contact[0]
            
            # Make the call
            speak_text(f"Calling {final_contact_name}")
            eel.receiveRecognitionResult(f"Calling {final_contact_name}")()
            
            success, result_msg = make_whatsapp_call(final_contact_name, "voice")
            
            if success:
                speak_text("Call started")
                eel.receiveRecognitionResult(f"✅ {result_msg}")()
            else:
                speak_text("Call failed")
                eel.receiveRecognitionResult(f"❌ {result_msg}")()
        
        # Video call flow
        elif "video call" in query_lower:
            # Ask for contact name
            contact_name = None
            selected_contact = None
            in_number_selection = False
            current_matches = []
            
            for attempt in range(2):
                if in_number_selection:
                    speak_text("Say the number")
                    eel.receiveRecognitionResult("Which number?")()
                elif attempt == 0:
                    speak_text("Who do you want to video call?")
                    eel.receiveRecognitionResult("Video call who?")()
                else:
                    speak_text("Say the name again")
                    eel.receiveRecognitionResult("Try again")()
                
                # Get contact name or number
                contact_response = takecommand()
                
                if contact_response:
                    # If we're in number selection mode
                    if in_number_selection:
                        import re
                        numbers = re.findall(r'\d+', contact_response)
                        if numbers:
                            choice_num = int(numbers[0])
                            if 1 <= choice_num <= len(current_matches):
                                selected_contact = current_matches[choice_num - 1]
                                break
                        
                        # If no number, try name matching
                        for contact in current_matches:
                            if contact_response.lower() in contact[0].lower():
                                selected_contact = contact
                                break
                        if selected_contact:
                            break
                        continue
                    
                    # First time or retry - get contact name
                    contact_name = contact_response.strip()
                    
                    # Get all matching contacts
                    matching_contacts = get_all_matching_contacts(contact_name)
                    
                    if len(matching_contacts) == 0:
                        speak_text(f"Contact {contact_name} not found")
                        contact_name = None
                    elif len(matching_contacts) == 1:
                        selected_contact = matching_contacts[0]
                        break
                    else:
                        # Multiple matches - show numbered options
                        current_matches = matching_contacts
                        in_number_selection = True
                        
                        options_text = ""
                        for i, contact in enumerate(matching_contacts[:5], 1):
                            options_text += f"{i}. {contact[0]}, "
                        options_text = options_text.rstrip(", ")
                        
                        speak_text(f"Multiple contacts found. Say the number: {options_text}")
                        eel.receiveRecognitionResult(f"Say number: {options_text}")()
                        
                        # Get number choice
                        choice_response = takecommand()
                        if choice_response:
                            # Try to extract number from response
                            import re
                            numbers = re.findall(r'\d+', choice_response)
                            if numbers:
                                choice_num = int(numbers[0])
                                if 1 <= choice_num <= len(matching_contacts):
                                    selected_contact = matching_contacts[choice_num - 1]
                                    break
                            
                            # If no number, try name matching
                            for contact in matching_contacts:
                                if choice_response.lower() in contact[0].lower():
                                    selected_contact = contact
                                    break
                            if selected_contact:
                                break
            
            if not selected_contact:
                speak_text("Couldn't find contact. Cancelling.")
                eel.receiveRecognitionResult("❌ Cancelled")()
                return
            
            final_contact_name = selected_contact[0]
            
            # Make the call
            speak_text(f"Video calling {final_contact_name}")
            eel.receiveRecognitionResult(f"Video calling {final_contact_name}")()
            
            success, result_msg = make_whatsapp_call(final_contact_name, "video")
            
            if success:
                speak_text("Video call started")
                eel.receiveRecognitionResult(f"✅ {result_msg}")()
            else:
                speak_text("Call failed")
                eel.receiveRecognitionResult(f"❌ {result_msg}")()
        
        else:
            # Just open WhatsApp
            speak_text("Opening WhatsApp")
            eel.receiveRecognitionResult("Opening WhatsApp")()
            open_whatsapp_desktop()

