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
        self.api_key   = ELEVEN_API_KEY
        self.voice_id  = VOICE_ID or "pNInz6obpgDQGcFmaJgB"
        self._edge_voice = "en-US-GuyNeural"
        self._stop_flag  = False
        self.is_speaking = False
        self.subtitle_callback = subtitle_callback

        os.environ["SDL_AUDIODRIVER"] = "directsound"
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.mixer.init()

    # ── Subtitle helper — call once per full response ─────────────────────────

    def _fire_subtitle(self, text: str):
        if self.subtitle_callback and text.strip():
            try:
                self.subtitle_callback(text.strip())
            except Exception as e:
                if DEBUG:
                    print(f"[{ASSISTANT_NAME}] Subtitle callback error: {e}")

    # ── Public API ────────────────────────────────────────────────────────────

    def speak(self, text: str):
        if not text.strip():
            return
        self._stop_flag  = False
        self.is_speaking = True
        self._fire_subtitle(text)          # once, before playback
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
        Subtitle is fired ONCE with the full accumulated text after all
        sentences are collected, so the GUI never double-renders.
        """
        self._stop_flag  = False
        self.is_speaking = True
        audio_queue      = queue.Queue()
        full_text        = []          # accumulate for a single subtitle call

        def _producer():
            buffer       = ""
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
                            full_text.append(sentence)
                            audio_queue.put(sentence)
                    buffer = parts[-1]
            if buffer.strip() and not self._stop_flag:
                full_text.append(buffer.strip())
                audio_queue.put(buffer.strip())
            audio_queue.put(None)

        def _consumer():
            while True:
                sentence = audio_queue.get()
                if sentence is None:
                    break
                if self._stop_flag:
                    while not audio_queue.empty():
                        try:
                            audio_queue.get_nowait()
                        except Exception:
                            break
                    break
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

        # Fire subtitle ONCE with everything Marcus said
        self._fire_subtitle(" ".join(full_text))

    def speak_chunked(self, text: str):
        self.speak(text)

    # ── TTS backends ──────────────────────────────────────────────────────────

    def _elevenlabs(self, text: str) -> bool:
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
        self._stop_flag  = True
        self.is_speaking = False
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass

    def set_subtitle_callback(self, callback):
        self.subtitle_callback = callback