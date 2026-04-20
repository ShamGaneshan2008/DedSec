"""
elevenlabs_voice.py — drop-in ElevenLabs replacement for pyttsx3.

Usage in main.py:
    from elevenlabs_voice import speak
    speak("Hello, I am Marcus.")

Requires:
    pip install elevenlabs
    ELEVENLABS_API_KEY in your .env file
    ELEVENLABS_VOICE_ID in your .env (optional, defaults to Marcus-like voice)
"""

import os
import io
import threading
from dotenv import load_dotenv

load_dotenv()

API_KEY  = os.getenv("ELEVENLABS_API_KEY", "")
VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "IRHApOXLvnW57QJPQH2P")  # Josh — deep, clear
MODEL_ID = "eleven_monolingual_v1"

_client = None

def _get_client():
    global _client
    if _client is None:
        try:
            from elevenlabs.client import ElevenLabs
            _client = ElevenLabs(api_key=API_KEY)
        except ImportError:
            raise ImportError("Run: pip install elevenlabs")
    return _client

def speak(text: str, block: bool = False):
    """Speak text via ElevenLabs. Non-blocking by default."""
    if not text or not text.strip():
        return
    if not API_KEY:
        _fallback_speak(text)
        return
    t = threading.Thread(target=_speak_thread, args=(text,), daemon=True)
    t.start()
    if block:
        t.join()

def _speak_thread(text: str):
    try:
        import pygame
        client = _get_client()
        audio = client.generate(text=text, voice=VOICE_ID, model=MODEL_ID)
        audio_bytes = b"".join(audio)
        pygame.mixer.init()
        sound = pygame.mixer.Sound(io.BytesIO(audio_bytes))
        sound.play()
        while pygame.mixer.get_busy():
            pygame.time.wait(50)
    except Exception as e:
        print(f"[ElevenLabs] Error: {e} — falling back to pyttsx3")
        _fallback_speak(text)

def _fallback_speak(text: str):
    """Falls back to pyttsx3 if ElevenLabs is unavailable."""
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty("rate", 165)
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"[Voice] pyttsx3 fallback also failed: {e}")
