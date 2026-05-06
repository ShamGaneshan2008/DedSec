import os
import io
import re
import asyncio
import tempfile
import threading
import queue

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
import pygame
import requests

from backend.marcus.config import (
    ASSISTANT_NAME, ELEVEN_API_KEY, VOICE_ID,
    TTS_RATE, TTS_VOLUME, DEBUG
)


class Speech:
    def __init__(self, subtitle_callback=None):
        """
        Initialize Speech engine with optional subtitle callback.

        Args:
            subtitle_callback: Optional function(text: str) called when text is spoken.
                              Used to update subtitles in real-time.
        """
        self.api_key = ELEVEN_API_KEY
        self.voice_id = VOICE_ID or "pNInz6obpgDQGcFmaJgB"
        self._edge_voice = "en-US-GuyNeural"
        self._stop_flag = False
        self.is_speaking = False  # True while audio is playing
        self.subtitle_callback = subtitle_callback  # NEW: Callback for subtitles

        os.environ["SDL_AUDIODRIVER"] = "directsound"
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.mixer.init()

    def speak(self, text: str):
        """Speak the given text and trigger subtitle callback."""
        if not text.strip():
            return
        self._stop_flag = False
        self.is_speaking = True

        # Trigger subtitle callback
        if self.subtitle_callback:
            try:
                self.subtitle_callback(text)
            except Exception as e:
                if DEBUG:
                    print(f"[{ASSISTANT_NAME}] Subtitle callback error: {e}")

        try:
            if self.api_key:
                if self._elevenlabs(text):
                    return
            self._edge_tts(text)
        finally:
            self.is_speaking = False

    def speak_stream(self, token_generator):
        """
        Streams tokens → sentences → audio.
        Respects _stop_flag at every stage for instant barge-in.
        NEW: Triggers subtitle callback for each sentence.
        """
        self._stop_flag = False
        self.is_speaking = True
        audio_queue = queue.Queue()

        def _producer():
            buffer = ""
            sentence_end = re.compile(r'(?<=[.!?])\s+')
            for token in token_generator:
                if self._stop_flag:
                    break
                buffer += token
                print(token, end="", flush=True)
                parts = sentence_end.split(buffer)
                if len(parts) > 1:
                    for sentence in parts[:-1]:
                        sentence = sentence.strip()
                        if sentence:
                            audio_queue.put(sentence)
                    buffer = parts[-1]
            if buffer.strip() and not self._stop_flag:
                audio_queue.put(buffer.strip())
            audio_queue.put(None)

        def _consumer():
            while True:
                sentence = audio_queue.get()
                if sentence is None:
                    break
                if self._stop_flag:
                    # drain the queue so producer doesn't block
                    while not audio_queue.empty():
                        try:
                            audio_queue.get_nowait()
                        except Exception:
                            break
                    break

                # NEW: Trigger subtitle callback for each sentence
                if self.subtitle_callback:
                    try:
                        self.subtitle_callback(sentence)
                    except Exception as e:
                        if DEBUG:
                            print(f"[{ASSISTANT_NAME}] Subtitle callback error: {e}")

                if self.api_key:
                    if self._elevenlabs(sentence):
                        continue
                self._edge_tts(sentence)

        print("\nMARCUS > ", end="", flush=True)

        producer_thread = threading.Thread(target=_producer, daemon=True)
        consumer_thread = threading.Thread(target=_consumer, daemon=True)

        producer_thread.start()
        consumer_thread.start()

        producer_thread.join()
        consumer_thread.join()
        print()
        self.is_speaking = False

    def speak_chunked(self, text: str):
        """Speak text in chunks (delegates to speak)."""
        self.speak(text)

    def _elevenlabs(self, text: str) -> bool:
        """Generate and play speech using ElevenLabs API."""
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        data = {
            "text": text,
            "model_id": "eleven_turbo_v2_5",
            "voice_settings": {
                "stability": 0.40,
                "similarity_boost": 0.75,
                "style": 0.35,
                "use_speaker_boost": True
            }
        }
        try:
            response = requests.post(url, json=data, headers=headers, timeout=15)
            if response.status_code == 200:
                audio_stream = io.BytesIO(response.content)
                pygame.mixer.music.load(audio_stream)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    if self._stop_flag:
                        pygame.mixer.music.stop()
                        break
                    pygame.time.Clock().tick(10)
                return True
            else:
                if DEBUG:
                    print(f"\n[{ASSISTANT_NAME}] ElevenLabs {response.status_code}:", response.text[:80])
                return False
        except requests.exceptions.Timeout:
            if DEBUG:
                print(f"\n[{ASSISTANT_NAME}] ElevenLabs timed out.")
            return False
        except Exception as e:
            if DEBUG:
                print(f"\n[{ASSISTANT_NAME}] ElevenLabs error: {e}")
            return False

    def _edge_tts(self, text: str):
        """Generate and play speech using Edge TTS (fallback)."""
        try:
            import edge_tts

            async def _run():
                communicate = edge_tts.Communicate(text, self._edge_voice)
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                    tmp_path = f.name
                await communicate.save(tmp_path)
                return tmp_path

            tmp_path = asyncio.run(_run())
            pygame.mixer.music.load(tmp_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                if self._stop_flag:
                    pygame.mixer.music.stop()
                    break
                pygame.time.Clock().tick(10)
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

        except ImportError:
            print(f"[{ASSISTANT_NAME}] edge-tts not installed. Run: pip install edge-tts")
            self._pyttsx3_fallback(text)
        except Exception as e:
            if DEBUG:
                print(f"[{ASSISTANT_NAME}] edge-tts error: {e}")
            self._pyttsx3_fallback(text)

    def _pyttsx3_fallback(self, text: str):
        """Final fallback using pyttsx3 (offline TTS)."""
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty("rate", TTS_RATE)
            engine.setProperty("volume", TTS_VOLUME)
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            print(f"[{ASSISTANT_NAME}] All TTS failed: {e}")

    def stop(self):
        """Interrupt playback immediately."""
        self._stop_flag = True
        self.is_speaking = False
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass

    def set_subtitle_callback(self, callback):
        """
        Set or update the subtitle callback function.

        Args:
            callback: Function(text: str) to be called when text is spoken.
        """
        self.subtitle_callback = callback