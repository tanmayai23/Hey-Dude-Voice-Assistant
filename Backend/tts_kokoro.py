"""Cloud TTS via Kokoro-82M on DeepInfra.

Why cloud: laptop has no GPU and limited RAM, so running torch + the 327MB
Kokoro weights locally would slow things down. DeepInfra gives us the same
voice (warm, natural af_heart) for ~$0.06/hour of audio with ~500ms latency.

Short phrases (≤80 chars) are cached on disk so repeated lines like
"Ji boss" or "Done boss" play instantly without an API call.
"""
import hashlib
import os
import tempfile
import threading
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()

DEEPINFRA_API_KEY = os.getenv('DEEPINFRA_API_KEY', '').strip()
KOKORO_VOICE = os.getenv('KOKORO_VOICE', 'af_heart').strip() or 'af_heart'
KOKORO_MODEL = 'hexgrad/Kokoro-82M'
KOKORO_ENDPOINT = 'https://api.deepinfra.com/v1/openai/audio/speech'

_CACHE_DIR = Path(__file__).resolve().parent / 'tts_cache'
_CACHE_MAX_TEXT_LEN = 80
_REQUEST_TIMEOUT = 15

_cache_lock = threading.Lock()


def is_configured() -> bool:
    return bool(DEEPINFRA_API_KEY)


def _cache_path(text: str, voice: str) -> Path:
    key = f"{KOKORO_MODEL}|{voice}|{text}".encode('utf-8')
    digest = hashlib.sha1(key).hexdigest()
    return _CACHE_DIR / f"{digest}.wav"


def _fetch_wav(text: str, voice: str) -> bytes:
    resp = requests.post(
        KOKORO_ENDPOINT,
        headers={
            'Authorization': f'Bearer {DEEPINFRA_API_KEY}',
            'Content-Type': 'application/json',
        },
        json={
            'model': KOKORO_MODEL,
            'input': text,
            'voice': voice,
            'response_format': 'wav',
        },
        timeout=_REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.content


def synthesize_to_file(text: str, voice: Optional[str] = None) -> str:
    """Return a path to a WAV file containing speech for `text`. Raises on
    network/API failure so the caller can fall back to pyttsx3."""
    if not text:
        raise ValueError("empty text")
    if not DEEPINFRA_API_KEY:
        raise RuntimeError("DEEPINFRA_API_KEY not set")

    voice = (voice or KOKORO_VOICE).strip() or 'af_heart'
    use_cache = len(text) <= _CACHE_MAX_TEXT_LEN
    cached = _cache_path(text, voice) if use_cache else None

    if cached and cached.exists():
        return str(cached)

    wav_bytes = _fetch_wav(text, voice)

    if cached:
        with _cache_lock:
            _CACHE_DIR.mkdir(parents=True, exist_ok=True)
            tmp = cached.with_suffix('.wav.tmp')
            tmp.write_bytes(wav_bytes)
            os.replace(tmp, cached)
        return str(cached)

    # Long text — write to OS temp dir and let the OS reap it.
    fd, path = tempfile.mkstemp(prefix='jarvis_tts_', suffix='.wav')
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(wav_bytes)
    except Exception:
        try: os.unlink(path)
        except OSError: pass
        raise
    return path
