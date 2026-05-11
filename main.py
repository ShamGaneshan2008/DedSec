import os
import sys
import json
import threading
from dotenv import load_dotenv
from backend.marcus.core.ai import AI
from backend.marcus.core.router import Router
from backend.marcus.core.memory import Memory
from backend.marcus.utils.speech import Speech

load_dotenv()

MEMORY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend/data/memory.json")


def _load_raw() -> dict:
    try:
        with open(MEMORY_PATH, "r") as f:
            data = json.load(f)
        if isinstance(data, list):
            data = {"user_name": None, "events": data}
        return data
    except (FileNotFoundError, json.JSONDecodeError):
        return {"user_name": None, "events": []}


def _save_raw(data: dict):
    os.makedirs(os.path.dirname(MEMORY_PATH), exist_ok=True)
    with open(MEMORY_PATH, "w") as f:
        json.dump(data, f, indent=2)


def get_user_name() -> str | None:
    return _load_raw().get("user_name")


def set_user_name(name: str):
    data = _load_raw()
    data["user_name"] = name.strip().title()
    _save_raw(data)


def resolve_user_name(interactive: bool = True) -> str:
    name = get_user_name()
    if name:
        return name
    if not interactive:
        return "Operative"
    print("[MARCUS] I don't have your name on file.")
    raw = input("[MARCUS] What should I call you? > ").strip()
    if raw:
        set_user_name(raw)
        name = raw.title()
        print(f"[MARCUS] Got it. Good to meet you, {name}.\n")
        return name
    return "Operative"


def _patch_router_env(name: str):
    os.environ["MARCUS_USER_NAME"] = name


def _check_mic(device_index: int) -> bool:
    """Check mic using the SAME device index Listener will use."""
    try:
        import speech_recognition as sr
        with sr.Microphone(device_index=device_index) as source:
            pass
        return True
    except Exception as e:
        print(f"[MARCUS] Mic check failed (device {device_index}): {e}")
        return False


def _get_mic_index() -> int:
    """Mirror the same logic as listener.py get_mic()."""
    try:
        import speech_recognition as sr
        for i, name in enumerate(sr.Microphone.list_microphone_names()):
            if "jlab" in name.lower() and "headset" in name.lower():
                return i
    except Exception:
        pass
    return 0


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

    user_name = resolve_user_name(interactive=True)
    _patch_router_env(user_name)

    memory = Memory()
    ai     = AI(memory)

    # Resolve mic index first — before Speech initializes pygame/SDL
    mic_index     = _get_mic_index()
    mic_available = _check_mic(mic_index)

    # Speech init AFTER mic check — pygame mixer can interfere with PyAudio on Windows
    speech = Speech()
    router = Router(ai, memory, speech=speech)

    if mic_available:
        from backend.marcus.utils.listener import Listener
        listener = Listener(router, speech)
        print(f"[MARCUS] ctOS link established. Say 'Hey Marcus' to activate, {user_name}.\n")
        listener.start_wake_word_loop()
    else:
        print(f"[MARCUS] No mic detected. Dropping into text input mode.")
        _text_fallback_loop(router, speech, user_name)


def _text_fallback_loop(router, speech, user_name: str = "Operative"):
    print(f"[MARCUS] Text mode active. Type your command, {user_name}. ('quit' to exit)\n")

    while True:
        try:
            user_input = input("YOU    > ").strip()
            if not user_input:
                continue

            if user_input.lower().startswith("my name is "):
                new_name = user_input[11:].strip().title()
                set_user_name(new_name)
                _patch_router_env(new_name)
                user_name = new_name
                print(f"[MARCUS] Updated. I'll call you {new_name} from now on.\n")
                continue

            if user_input.lower() in ("quit", "exit", "go dark", "bye", "goodbye"):
                print(f"[MARCUS] Going dark. DedSec out, {user_name}.")
                break

            response = router.handle(user_input)
            print(f"MARCUS > {response}\n")

            threading.Thread(
                target=speech.speak_chunked,
                args=(response,),
                daemon=True
            ).start()

        except (KeyboardInterrupt, EOFError):
            print("\n[MARCUS] Signal lost. DedSec out.")
            break


if __name__ == "__main__":
    if "--cmd" in sys.argv:
        idx = sys.argv.index("--cmd")
        if idx + 1 < len(sys.argv):
            cmd = sys.argv[idx + 1]
            load_dotenv()

            user_name = resolve_user_name(interactive=False)
            _patch_router_env(user_name)

            memory = Memory()
            ai     = AI(memory)
            speech = Speech()
            router = Router(ai, memory, speech=speech)

            from backend.marcus import resolve as expand_shortcut, handle_meta_command
            handled, meta_response = handle_meta_command(cmd)
            if handled:
                print(meta_response, flush=True)
                sys.exit(0)

            cmd    = expand_shortcut(cmd)
            result = router.handle_stream(cmd)

            if hasattr(result, '__iter__') and not isinstance(result, str):
                for token in result:
                    print(token, end="", flush=True)
                print()
            else:
                print(result, flush=True)
        else:
            print("[ERROR] --cmd flag provided but no command given.", flush=True)
    else:
        main()