import os
import requests
import pygame
from marcus.config import ASSISTANT_NAME

ELEVEN_API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "TxGEqnHWrfWFTfGW9XjX")
print("VOICE USED:", VOICE_ID)

class Speech:
    def __init__(self):
        try:
            pygame.mixer.init()
        except Exception as e:
            print(f"[{ASSISTANT_NAME}] Audio init failed: {e}")

    def speak(self, text: str):
        if not ELEVEN_API_KEY:
            print(f"[{ASSISTANT_NAME}] No ElevenLabs key. Using fallback.")
            return

        try:
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"

            headers = {
                "xi-api-key": ELEVEN_API_KEY,
                "Content-Type": "application/json"
            }

            data = {
                "text": text,
                "model_id": "eleven_monolingual_v1"
            }

            response = requests.post(url, json=data, headers=headers)

            if response.status_code != 200:
                print(f"[{ASSISTANT_NAME}] ElevenLabs error:", response.text)
                return

            with open("voice.mp3", "wb") as f:
                f.write(response.content)

            pygame.mixer.music.load("voice.mp3")
            pygame.mixer.music.play()

            while pygame.mixer.music.get_busy():
                continue

        except Exception as e:
            print(f"[{ASSISTANT_NAME}] Voice error:", e)