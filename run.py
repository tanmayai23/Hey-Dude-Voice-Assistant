"""Run launcher: starts the Hey Dude voice assistant.

Hotword detection runs in a background thread and listens for "Hey Dude".
The microphone will only activate when the wake word is detected.
"""

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)

import multiprocessing
import os
import sys


def start():
    """Start the Hey Dude GUI application with face authentication."""
    print("="*50)
    print("🔐 Hey Dude - Face Authentication")
    print("="*50)
    
    # Check if face authentication should be used
    skip_auth = os.getenv('SKIP_FACE_AUTH', 'false').lower() == 'true'
    
    if not skip_auth:
        try:
            # Import face authentication
            from Backend.auth.recognize import AuthenticateFace
            
            # Authenticate user
            authenticated = AuthenticateFace()
            
            if not authenticated:
                print("\n❌ Authentication Failed! Exiting...\n")
                input("Press Enter to exit...")
                sys.exit(1)
            
            print("\n✅ Authentication Successful!\n")
            
        except FileNotFoundError:
            print("\n⚠️  Face recognition model not found.")
            print("Please run the following commands first:")
            print("1. python Backend/auth/sample.py")
            print("2. python Backend/auth/trainer.py\n")
            
            choice = input("Continue without authentication? (y/n): ").lower()
            if choice != 'y':
                sys.exit(1)
        
        except Exception as e:
            print(f"\n⚠️  Face authentication error: {e}")
            choice = input("Continue without authentication? (y/n): ").lower()
            if choice != 'y':
                sys.exit(1)
    else:
        print("\n⚠️  Face authentication skipped (SKIP_FACE_AUTH=true)\n")
    
    # Start the application
    print("="*50)
    print("🚀 Starting Hey Dude Voice Assistant")
    print("="*50)
    
    # Import locally to avoid issues at module load time
    from main import start as app_start
    app_start()


if __name__ == '__main__':
    # Set spawn method for Windows compatibility
    multiprocessing.freeze_support()
    start()