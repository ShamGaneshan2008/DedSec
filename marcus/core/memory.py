import json
import os
from marcus.config import MEMORY_FILE, MEMORY_LIMIT


def _load_memory() -> list:
    if not os.path.exists(MEMORY_FILE):
        return []
    with open(MEMORY_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def _save_memory(data: list):
    os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)
    with open(MEMORY_FILE, "w") as f:
        json.dump(data, f, indent=2)


def get_recent_memory() -> list:
    """Return the last N exchanges for AI context."""
    memory = _load_memory()
    return memory[-MEMORY_LIMIT:]


def save_exchange(user_input: str, ai_response: str):
    """Append a user/AI exchange to memory."""
    memory = _load_memory()
    memory.append({
        "user": user_input,
        "ai": ai_response
    })
    _save_memory(memory)


def clear_memory():
    """Wipe all memory."""
    _save_memory([])
    return "Memory cleared."