import speech_recognition as sr
from marcus.config import MIC_TIMEOUT, MIC_PHRASE_LIMIT, ASSISTANT_NAME

recognizer = sr.Recognizer()


def listen() -> str | None:
    """Listen via microphone and return transcribed text."""
    with sr.Microphone() as source:
        print(f"[{ASSISTANT_NAME}] Listening...")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)

        try:
            audio = recognizer.listen(
                source,
                timeout=MIC_TIMEOUT,
                phrase_time_limit=MIC_PHRASE_LIMIT
            )
            text = recognizer.recognize_google(audio)
            print(f"[You] {text}")
            return text

        except sr.WaitTimeoutError:
            print(f"[{ASSISTANT_NAME}] No input detected.")
            return None

        except sr.UnknownValueError:
            print(f"[{ASSISTANT_NAME}] Couldn't understand that.")
            return None

        except sr.RequestError as e:
            print(f"[{ASSISTANT_NAME}] Speech service error: {e}")
            return None