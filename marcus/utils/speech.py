import pyttsx3
from marcus.config import TTS_RATE, TTS_VOLUME, TTS_VOICE_INDEX, ASSISTANT_NAME

engine = pyttsx3.init()
engine.setProperty("rate", TTS_RATE)
engine.setProperty("volume", TTS_VOLUME)

voices = engine.getProperty("voices")
if voices:
    engine.setProperty("voice", voices[TTS_VOICE_INDEX].id)


def speak(text: str):
    """Speak text aloud and print it."""
    print(f"[{ASSISTANT_NAME}] {text}")
    engine.say(text)
    engine.runAndWait()