import os
from dotenv import load_dotenv
from marcus.core.ai import AI
from marcus.core.router import Router
from marcus.core.memory import Memory
from marcus.utils.speech import Speech

load_dotenv()

def main():
    print("""
    ███╗   ███╗ █████╗ ██████╗  ██████╗██╗   ██╗███████╗
    ████╗ ████║██╔══██╗██╔══██╗██╔════╝██║   ██║██╔════╝
    ██╔████╔██║███████║██████╔╝██║     ██║   ██║███████╗
    ██║╚██╔╝██║██╔══██║██╔══██╗██║     ██║   ██║╚════██║
    ██║ ╚═╝ ██║██║  ██║██║  ██║╚██████╗╚██████╔╝███████║
    ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚══════╝
         V.A — DedSec Intelligence Layer | by Marcus
    """)

    memory = Memory()
    ai = AI(memory)
    speech = Speech()
    router = Router(ai, memory, speech=speech)

    # Try voice mode, fall back to text if mic unavailable
    mic_available = False
    try:
        import speech_recognition as sr
        test_mic = sr.Microphone()
        with test_mic as source:
            pass
        mic_available = True
    except Exception as e:
        print(f"[MARCUS] Mic check failed: {e}")

    if mic_available:
        from marcus.utils.listener import Listener
        listener = Listener(router, speech)
        print("[MARCUS] ctOS link established. Say 'Hey Marcus' to activate.\n")
        listener.start_wake_word_loop()
    else:
        print("[MARCUS] No mic detected. Dropping into text input mode.")
        _text_fallback_loop(router, speech)


def _text_fallback_loop(router, speech):
    print("[MARCUS] Text mode active. Type your command. ('quit' to exit)\n")
    while True:
        try:
            user_input = input("YOU    > ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("quit", "exit", "go dark", "bye", "goodbye"):
                print("[MARCUS] Going dark. DedSec out.")
                break
            response = router.handle(user_input)
            print(f"MARCUS > {response}\n")
            speech.speak(response)
        except (KeyboardInterrupt, EOFError):
            print("\n[MARCUS] Signal lost. DedSec out.")
            break


if __name__ == "__main__":
    main()
