"""Picovoice Porcupine wake-word detector — true offline, near-zero CPU at idle.

Why this over the speech_recognition fallback in hotword_detection.py:
- Runs fully offline (no Google round-trip per phrase).
- ~1% CPU on a single core, ~10 MB RAM. Safe for low-spec laptops.
- Custom keywords trainable on console.picovoice.ai (paste 'Hey Boss' .ppn into
  WAKE_WORD_PPN_PATH). Until then we fall back to a built-in keyword.

The detector runs in a daemon thread; on each detection it calls
`activateMicFromHotword()` in the Eel frontend AND `start_listen()` so the
existing in-page mic flow handles transcription.
"""
import os
import threading
import time


_thread = None
_stop_flag = threading.Event()


def _build_porcupine():
    """Returns (porcupine, recorder) ready to read frames, or raises."""
    import pvporcupine
    from pvrecorder import PvRecorder

    access_key = os.getenv('PICOVOICE_ACCESS_KEY', '').strip()
    if not access_key:
        raise RuntimeError(
            "PICOVOICE_ACCESS_KEY not set in .env — get a free key at "
            "https://console.picovoice.ai/"
        )

    ppn_path = os.getenv('WAKE_WORD_PPN_PATH', '').strip()

    if ppn_path and os.path.exists(ppn_path):
        # Custom keyword (e.g. trained 'Hey Boss')
        porcupine = pvporcupine.create(
            access_key=access_key,
            keyword_paths=[ppn_path],
            sensitivities=[0.6],
        )
        print(f"🎯 Porcupine ready with custom keyword: {os.path.basename(ppn_path)}")
    else:
        # Built-in fallback so the user gets *something* working immediately.
        # 'jarvis' is shipped with pvporcupine — fitting for our boss persona.
        builtin = os.getenv('WAKE_WORD_BUILTIN', 'jarvis').strip().lower()
        porcupine = pvporcupine.create(
            access_key=access_key,
            keywords=[builtin],
            sensitivities=[0.6],
        )
        print(
            f"🎯 Porcupine ready with built-in keyword: '{builtin}'. "
            "Train custom 'Hey Boss' at console.picovoice.ai and set "
            "WAKE_WORD_PPN_PATH for the real persona."
        )

    recorder = PvRecorder(
        device_index=-1,
        frame_length=porcupine.frame_length,
    )
    recorder.start()
    return porcupine, recorder


def _on_detect(eel_instance):
    """Fire UI mic activation + backend listener. Called from detector thread."""
    try:
        # Frontend animation / wave / mic UI on
        eel_instance.activateMicFromHotword()
    except Exception as e:
        print(f"⚠️  activateMicFromHotword failed: {e}")
    try:
        # Backend recognizer for cases where the browser SR isn't running
        # (eg. user is on another tab). The frontend SR will also pick up
        # if the page is focused — both is fine; the second wins.
        from Backend.command import start_listen
        start_listen()
    except Exception as e:
        print(f"⚠️  start_listen failed: {e}")


def _run(eel_instance):
    """Detector loop. Runs until _stop_flag is set or process exits."""
    porcupine = recorder = None
    try:
        porcupine, recorder = _build_porcupine()
        # Debounce so a single 'hey boss' doesn't fire twice.
        last_fire = 0.0
        DEBOUNCE_S = 2.0

        while not _stop_flag.is_set():
            try:
                pcm = recorder.read()
                idx = porcupine.process(pcm)
                if idx >= 0:
                    now = time.time()
                    if now - last_fire >= DEBOUNCE_S:
                        last_fire = now
                        print("✅ Wake word detected (Porcupine)")
                        _on_detect(eel_instance)
            except Exception as inner:
                print(f"⚠️  Porcupine read error: {inner}")
                time.sleep(0.2)
    except Exception as e:
        print(f"❌ Porcupine init failed: {e}")
        raise
    finally:
        try:
            if recorder is not None:
                recorder.stop()
                recorder.delete()
        except Exception:
            pass
        try:
            if porcupine is not None:
                porcupine.delete()
        except Exception:
            pass


def start(eel_instance):
    """Spin up the Porcupine listener in a daemon thread.

    Returns True if the thread started cleanly, False otherwise. The caller
    should fall back to the speech_recognition based hotword detector if this
    returns False.
    """
    global _thread

    # Probe imports first so we can fall back cleanly without leaving a thread.
    try:
        import pvporcupine  # noqa: F401
        from pvrecorder import PvRecorder  # noqa: F401
    except ImportError as e:
        print(f"ℹ️  Porcupine not installed ({e}); falling back to speech_recognition hotword.")
        return False

    if not os.getenv('PICOVOICE_ACCESS_KEY', '').strip():
        print("ℹ️  PICOVOICE_ACCESS_KEY missing; falling back to speech_recognition hotword.")
        return False

    _stop_flag.clear()
    _thread = threading.Thread(target=_run, args=(eel_instance,), daemon=True)
    _thread.start()
    return True


def stop():
    _stop_flag.set()
