"""Hey Dude / Jarvis launcher.

By default this skips face authentication (SKIP_FACE_AUTH=true in .env)
so OpenCV is never loaded — saves ~150 MB of RAM at startup. Set
SKIP_FACE_AUTH=false in .env to enable webcam-based login."""
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)

import multiprocessing
import os
import sys

from dotenv import load_dotenv
load_dotenv()


def start():
    skip_auth = os.getenv('SKIP_FACE_AUTH', 'true').lower() == 'true'

    if not skip_auth:
        print("=" * 50)
        print("🔐 Hey Dude - Face Authentication")
        print("=" * 50)
        try:
            # Import lazily so cv2 isn't loaded when face-auth is disabled.
            from Backend.auth.recognize import AuthenticateFace

            authenticated = AuthenticateFace()

            if not authenticated:
                print("\n❌ Authentication failed. Exiting.\n")
                input("Press Enter to exit...")
                sys.exit(1)
            print("\n✅ Authentication successful!\n")

        except FileNotFoundError:
            print("\n⚠️  Face recognition model not found. To set up:")
            print("    1. python Backend/auth/sample.py")
            print("    2. python Backend/auth/trainer.py\n")
            choice = input("Continue without authentication? (y/n): ").lower()
            if choice != 'y':
                sys.exit(1)

        except Exception as e:
            print(f"\n⚠️  Face auth error: {e}")
            choice = input("Continue without authentication? (y/n): ").lower()
            if choice != 'y':
                sys.exit(1)
    else:
        print("ℹ️  Face authentication skipped (SKIP_FACE_AUTH=true).")

    # Defer main import so .env is loaded and any auth import errors above
    # don't prevent the app from starting.
    from main import start as app_start
    app_start()


if __name__ == '__main__':
    multiprocessing.freeze_support()
    start()
