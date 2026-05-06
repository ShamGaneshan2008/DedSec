import io
import os
import time
import random
import wave
import audioop
import threading
import speech_recognition as sr
from groq import Groq
from dotenv import load_dotenv

for i, name in enumerate(sr.Microphone.list_microphone_names()):
    print(f"[{i}] {name}")

load_dotenv()

WAKE_WORDS = [
    "hey marcus", "hey market", "hey mark", "markus",
    "marcus", "mark", "hey marx", "hey marca",
    "margaris", "hey margaris", "margarous", "marquis",
    "hey marquis", "markets", "hey markets",
]

WAKE_RESPONSES     = ["Yeah?", "What's up?", "Go ahead.", "I'm here.", "Talk to me.", "Mm?"]
THINKING_FILLERS   = ["Mm, one sec.", "Let me think.", "Yeah, hold on.", "Give me a second.", "On it.", "Right."]
IDLE_CHECKINS      = ["You still there?", "Still with me?", "Did you need something else?"]
GOODBYE_RESPONSES  = ["Later.", "Got it, going quiet.", "I'll be around.", "Alright, stepping back."]
BARGE_IN_ACK       = ["Sure, go ahead.", "Yeah?", "What's up?", "I'm listening."]


BARGE_IN_RMS     = 800    # tune: run calibration below if unsure
FILLER_MIN_DELAY = 0.8

def get_mic():
    names = sr.Microphone.list_microphone_names()
    for i, name in enumerate(names):
        if "jlab" in name.lower() and "headset" in name.lower():
            return i
    return 0

MIC_INDEX = get_mic()


class Listener:
    def __init__(self, router, speech):
        self.router = router
        self.speech = speech
        self.recognizer = sr.Recognizer()

        self.recognizer.pause_threshold          = 0.6
        self.recognizer.non_speaking_duration    = 0.4
        self.recognizer.energy_threshold         = 550
        self.recognizer.dynamic_energy_threshold = False

        self.groq = Groq(api_key=os.getenv("GROQ_API_KEY"))

        self._barge_in_active = False
        self._barged          = False

        # import pyaudio once — used only by the barge-in monitor
        try:
            import pyaudio
            self._pa = pyaudio.PyAudio()
        except ImportError:
            print("[MARCUS] WARNING: pyaudio not installed. Barge-in disabled.")
            print("[MARCUS] Run:  pip install pyaudio")
            self._pa = None

    # ── Barge-in monitor ──────────────────────────────────────────────────────
    # Opens its OWN independent PyAudio stream on the same mic.
    # This does NOT conflict with speech_recognition's stream because
    # PyAudio can open multiple input streams on the same device simultaneously.

    def _start_barge_in_monitor(self):
        if self._pa is None:
            return  # pyaudio not available, skip

        self._barge_in_active = True
        self._barged = False

        def _monitor():
            import pyaudio
            stream = None
            try:
                stream = self._pa.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=16000,
                    input=True,
                    input_device_index=MIC_INDEX,
                    frames_per_buffer=512,
                )

                while self._barge_in_active:
                    try:
                        chunk = stream.read(512, exception_on_overflow=False)
                    except Exception:
                        time.sleep(0.01)
                        continue

                    rms = audioop.rms(chunk, 2)  # 2 bytes = paInt16

                    if rms > BARGE_IN_RMS and self._barge_in_active:
                        if self.speech.is_speaking:
                            print(f"\n[MARCUS] Barge-in (RMS {rms}). Stopping.")
                            self._barged = True
                            self.speech.stop()
                            self._barge_in_active = False
                            return

            except Exception as e:
                print(f"[MARCUS] Barge-in monitor error: {e}")
            finally:
                if stream:
                    try:
                        stream.stop_stream()
                        stream.close()
                    except Exception:
                        pass

        threading.Thread(target=_monitor, daemon=True).start()

    def _stop_barge_in_monitor(self):
        self._barge_in_active = False

    # ── Speech helpers ────────────────────────────────────────────────────────

    def _speak(self, text):
        self._start_barge_in_monitor()
        self.speech.speak(text)
        self._stop_barge_in_monitor()

    def _stream(self, generator_or_text):
        self._start_barge_in_monitor()
        if hasattr(generator_or_text, '__iter__') and not isinstance(generator_or_text, str):
            self.speech.speak_stream(generator_or_text)
        else:
            self.speech.speak(generator_or_text)
        self._stop_barge_in_monitor()

    def _thinking_filler(self, response_ready_event: threading.Event):
        if response_ready_event.wait(timeout=FILLER_MIN_DELAY):
            return
        self.speech.speak(random.choice(THINKING_FILLERS))

    # ── Wake word loop ────────────────────────────────────────────────────────

    def start_wake_word_loop(self):
        self.recognizer.energy_threshold = 600
        print(f"[MARCUS] Energy threshold: {self.recognizer.energy_threshold:.0f}")
        print("[MARCUS] Ready. Say 'Hey Marcus' to activate.\n")

        while True:
            try:
                audio = self._listen_once(timeout=None, phrase_limit=4)
                if audio is None:
                    continue

                duration = len(audio.get_raw_data()) / (audio.sample_rate * audio.sample_width)
                if duration < 0.8:
                    continue

                text = self._transcribe(audio)
                if text is None:
                    continue

                if len(text.split()) < 2 and not any(w == text.lower().strip() for w in ["marcus", "markus"]):
                    continue

                print(f"[HEARD] {text}")

                if any(w in text.lower() for w in WAKE_WORDS):
                    self._enter_conversation_mode()

            except KeyboardInterrupt:
                print("\n[MARCUS] Shutting down.")
                break
            except Exception as e:
                print(f"[MARCUS] Error: {e}")
                time.sleep(0.5)

    # ── Conversation mode ─────────────────────────────────────────────────────

    def _enter_conversation_mode(self):
        print("[MARCUS] Activated.\n")
        self._speak(random.choice(WAKE_RESPONSES))

        idle_rounds  = 0
        checkin_done = False

        while True:
            print("[MARCUS] Listening...")
            audio = self._listen_once(timeout=7, phrase_limit=20)

            if audio is None:
                idle_rounds += 1
                if idle_rounds == 1 and not checkin_done:
                    checkin_done = True
                    self._speak(random.choice(IDLE_CHECKINS))
                    continue
                if idle_rounds >= 3:
                    self._speak("I'll be around.")
                    print("[MARCUS] Timed out. Back to wake word mode.\n")
                    return
                continue

            duration = len(audio.get_raw_data()) / (audio.sample_rate * audio.sample_width)
            if duration < 0.8:
                continue

            text = self._transcribe(audio)
            if not text or len(text.strip()) < 2:
                idle_rounds += 1
                continue

            lower = text.lower()
            print(f"\nYOU    > {text}")

            idle_rounds  = 0
            checkin_done = False

            if any(w in lower for w in ["goodbye", "bye marcus", "go dark", "stop listening", "disconnect"]):
                self._speak(random.choice(GOODBYE_RESPONSES))
                print("[MARCUS] Back to wake word mode.\n")
                return

            # ── Fetch + filler in parallel ────────────────────────────────────
            response_container = [None]
            response_ready     = threading.Event()

            def _fetch():
                response_container[0] = self.router.handle_stream(text)
                response_ready.set()

            fetch_thread  = threading.Thread(target=_fetch, daemon=True)
            filler_thread = threading.Thread(
                target=self._thinking_filler, args=(response_ready,), daemon=True
            )

            fetch_thread.start()
            filler_thread.start()
            fetch_thread.join()
            filler_thread.join()

            if self._barged:
                self._barged = False
                time.sleep(0.15)
                self._speak(random.choice(BARGE_IN_ACK))
                continue

            self._stream(response_container[0])

            if self._barged:
                self._barged = False
                time.sleep(0.15)
                self._speak(random.choice(BARGE_IN_ACK))

    # ── Low-level listen / transcribe ─────────────────────────────────────────

    def _listen_once(self, timeout=5, phrase_limit=10):
        try:
            with sr.Microphone(device_index=MIC_INDEX) as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                audio = self.recognizer.listen(
                    source, timeout=timeout, phrase_time_limit=phrase_limit
                )
            return audio

        except sr.WaitTimeoutError:
            return None

        except Exception as e:
            print(f"[MARCUS] Mic error (device {MIC_INDEX}): {e}")
            time.sleep(0.5)
            return None

    def _transcribe(self, audio) -> str | None:
        try:
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(audio.sample_width)
                wf.setframerate(audio.sample_rate)
                wf.writeframes(audio.get_raw_data())
            wav_buffer.seek(0)
            wav_buffer.name = "audio.wav"

            result = self.groq.audio.transcriptions.create(
                model="whisper-large-v3-turbo",
                file=wav_buffer,
                language="en",
                response_format="verbose_json"
            )

            text = result.text.strip() if hasattr(result, 'text') else str(result).strip()
            if not text:
                return None

            HALLUCINATIONS = {
                "thank you", "thanks", "thank you.", "thanks.",
                "you", ".", ",", "hmm", "hm", "um", "uh",
                "bye", "bye.", "okay", "ok", "yes", "no",
                "good", "right", "sure", "well", "so",
                "i", "the", "a", "an", "and", "is", "it",
                "oh", "ah", "eh", "er", "mm", "mmm",
                "subscrib", "subscribe", "like and subscribe",
                "good father", "set it down", "ascension",
            }

            if text.lower().strip(".?,!") in HALLUCINATIONS:
                return None

            if len(text.split()) == 1 and text.lower().strip(".,!?") not in ["marcus", "markus"]:
                return None

            return text

        except Exception as e:
            if DEBUG_ON():
                print(f"[MARCUS] Whisper error: {e}")
            return self._transcribe_google(audio)

    def _transcribe_google(self, audio) -> str | None:
        try:
            return self.recognizer.recognize_google(audio)
        except sr.UnknownValueError:
            return None
        except Exception as e:
            print(f"[MARCUS] Google STT fallback error: {e}")
            return None

    def stop(self):
        try:
            import pygame
            pygame.mixer.music.stop()
        except Exception:
            pass


def DEBUG_ON():
    try:
        from backend.marcus.config import DEBUG  # FIXED: correct import path
        return DEBUG
    except Exception:
        return False