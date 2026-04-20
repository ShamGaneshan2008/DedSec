import os
import json
from datetime import datetime

MEMORY_FILE = os.path.join(os.path.dirname(__file__), "../../data/memory.json")
LOG_FILE = os.path.join(os.path.dirname(__file__), "../../conversation.log")

class Memory:
    def __init__(self):
        self.history = []
        self._ensure_files()
        self._load_memory()

    def _ensure_files(self):
        os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)
        if not os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, "w") as f:
                json.dump([], f)
        if not os.path.exists(LOG_FILE):
            with open(LOG_FILE, "w") as f:
                f.write(f"=== Marcus V.A Conversation Log ===\nCreated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

    def _load_memory(self):
        try:
            with open(MEMORY_FILE, "r") as f:
                self.history = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            self.history = []

    def get_history(self) -> list:
        # Return last 10 exchanges (20 messages) to keep context window sane
        return self.history[-20:]

    def add_exchange(self, user_input: str, ai_reply: str):
        # Add to in-memory history
        self.history.append({"role": "user", "content": user_input})
        self.history.append({"role": "assistant", "content": ai_reply})

        # Persist to memory.json
        try:
            with open(MEMORY_FILE, "w") as f:
                json.dump(self.history[-100:], f, indent=2)  # keep last 100 messages
        except Exception as e:
            print(f"[MARCUS] Memory write error: {e}")

        # ✅ Actually write to conversation.log (was broken before)
        self._write_log(user_input, ai_reply)

    def _write_log(self, user_input: str, ai_reply: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = (
            f"[{timestamp}]\n"
            f"  YOU    : {user_input}\n"
            f"  MARCUS : {ai_reply}\n"
            f"{'─' * 60}\n"
        )
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception as e:
            print(f"[MARCUS] Log write error: {e}")

    def clear(self):
        self.history = []
        with open(MEMORY_FILE, "w") as f:
            json.dump([], f)
        print("[MARCUS] Memory wiped. Fresh start, operative.")
