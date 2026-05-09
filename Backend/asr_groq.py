"""Cloud ASR via Whisper-large-v3 on Groq.

Why Groq: free tier covers 8 hours of audio per day (more than personal use
will ever need), and Groq's LPU chips run Whisper at ~200ms per clip — the
fastest hosted Whisper available. Drop-in replacement for the unofficial
Google endpoint that recognize_google() hits.

The mic capture stays in command.takecommand(). This module only handles
the recognition step: AudioData in, transcribed text out.
"""
import os
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv('GROQ_API_KEY', '').strip()
GROQ_WHISPER_MODEL = os.getenv('GROQ_WHISPER_MODEL', 'whisper-large-v3-turbo').strip() \
    or 'whisper-large-v3-turbo'
ASR_LANGUAGE = os.getenv('ASR_LANGUAGE', 'en').strip()  # '' = auto-detect
GROQ_ENDPOINT = 'https://api.groq.com/openai/v1/audio/transcriptions'

_REQUEST_TIMEOUT = 20


def is_configured() -> bool:
    return bool(GROQ_API_KEY)


def transcribe(audio_data, language: Optional[str] = None) -> str:
    """Transcribe a speech_recognition.AudioData object via Groq Whisper.

    Raises on any failure (no key, network error, non-200 response, empty
    text) so the caller can fall back to a different ASR.
    """
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY not set")

    wav_bytes = audio_data.get_wav_data()

    data = {'model': GROQ_WHISPER_MODEL, 'response_format': 'json'}
    lang = ASR_LANGUAGE if language is None else language
    if lang:
        data['language'] = lang

    resp = requests.post(
        GROQ_ENDPOINT,
        headers={'Authorization': f'Bearer {GROQ_API_KEY}'},
        files={'file': ('audio.wav', wav_bytes, 'audio/wav')},
        data=data,
        timeout=_REQUEST_TIMEOUT,
    )
    resp.raise_for_status()

    text = (resp.json().get('text') or '').strip()
    if not text:
        raise RuntimeError("Groq returned empty transcription")
    return text
