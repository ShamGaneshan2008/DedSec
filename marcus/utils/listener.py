import speech_recognition as sr
import threading
import time

WAKE_WORD = "hey marcus"

class Listener:
    def __init__(self, router, speech):
        self.router = router
        self.speech = speech
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.is_active = False  # True when in conversation mode after wake word

        # Tune for responsiveness
        self.recognizer.pause_threshold = 1.0
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True

    def start_wake_word_loop(self):
        """Main loop: always listening for wake word, then entering conversation mode."""
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            print("[MARCUS] Ambient noise calibrated. Listening for wake word...")

        while True:
            try:
                audio = self._listen_once(timeout=None, phrase_limit=4)
                if audio is None:
                    continue

                text = self._transcribe(audio)
                if text is None:
                    continue

                if WAKE_WORD in text.lower():
                    self._enter_conversation_mode()
                # else: just idle, waiting for wake word

            except KeyboardInterrupt:
                print("\n[MARCUS] Signal lost. DedSec out.")
                break
            except Exception as e:
                print(f"[MARCUS] Listener error: {e}")
                time.sleep(1)

    def _enter_conversation_mode(self):
        """After wake word detected, listen and respond until silence timeout."""
        self.speech.speak("Signal acquired. What's the mission?")
        print("[MARCUS] Wake word detected — entering conversation mode.")

        idle_rounds = 0
        max_idle = 3  # after 3 silent rounds, go back to wake word mode

        while idle_rounds < max_idle:
            audio = self._listen_once(timeout=6, phrase_limit=15)

            if audio is None:
                idle_rounds += 1
                print(f"[MARCUS] Idle {idle_rounds}/{max_idle}...")
                continue

            text = self._transcribe(audio)
            if text is None:
                idle_rounds += 1
                continue

            # Check if user is ending the session
            if any(word in text.lower() for word in ["goodbye", "bye marcus", "go dark", "disconnect"]):
                self.speech.speak("Going dark. DedSec out.")
                print("[MARCUS] Session ended. Back to wake word mode.")
                return

            idle_rounds = 0  # reset idle on valid input
            print(f"[YOU] {text}")
            response = self.router.handle(text)
            print(f"[MARCUS] {response}")
            self.speech.speak(response)

        print("[MARCUS] Session timed out. Back to listening for wake word.")
        self.speech.speak("Going quiet. Call me when you need me.")

    def _listen_once(self, timeout=5, phrase_limit=10):
        """Listen for a single audio chunk."""
        try:
            with self.microphone as source:
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_limit
                )
            return audio
        except sr.WaitTimeoutError:
            return None
        except Exception as e:
            print(f"[MARCUS] Mic error: {e}")
            return None

    def _transcribe(self, audio) -> str | None:
        """Convert audio to text using Google STT."""
        try:
            text = self.recognizer.recognize_google(audio)
            return text
        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            print(f"[MARCUS] STT service error: {e}")
            return None
