"""
shortcuts.py — personal command shortcut trainer for Marcus.

Shortcuts are stored in data/shortcuts.json.
Call resolve(user_input) before passing text to your AI — it
expands any matching shortcut into the full command.

Usage in main.py:
    from shortcuts import resolve, add_shortcut, list_shortcuts
    user_input = resolve(user_input)  # expand before AI call

Training new shortcuts (say this to Marcus or call directly):
    add_shortcut("open project", "open PyCharm at D:/Marcus_V.A")
    add_shortcut("morning", "tell me the weather, my calendar, and news headlines")
"""

import json
import os
import re

SHORTCUTS_FILE = os.path.join(os.path.dirname(__file__), "data", "shortcuts.json")

_DEFAULT_SHORTCUTS = {
    "open project":   "open PyCharm at D:/Marcus_V.A",
    "morning":        "tell me today's weather, my top 3 tasks, and one news headline",
    "go dark":        "enable stealth mode and mute all notifications",
    "status":         "give me a full system status report",
    "who am i":       "tell me my name, current project, and last memory entry",
}

def _load() -> dict:
    os.makedirs(os.path.dirname(SHORTCUTS_FILE), exist_ok=True)
    if not os.path.exists(SHORTCUTS_FILE):
        _save(_DEFAULT_SHORTCUTS)
        return dict(_DEFAULT_SHORTCUTS)
    with open(SHORTCUTS_FILE, "r") as f:
        return json.load(f)

def _save(shortcuts: dict):
    os.makedirs(os.path.dirname(SHORTCUTS_FILE), exist_ok=True)
    with open(SHORTCUTS_FILE, "w") as f:
        json.dump(shortcuts, f, indent=2)

def resolve(text: str) -> str:
    """
    Check if text matches a shortcut (case-insensitive, strips punctuation).
    Returns the expanded command if matched, original text otherwise.
    """
    cleaned = re.sub(r"[^\w\s]", "", text.strip().lower())
    shortcuts = _load()
    for key, expansion in shortcuts.items():
        if cleaned == key.lower():
            print(f"[Shortcuts] '{text}' → '{expansion}'")
            return expansion
    return text

def add_shortcut(trigger: str, expansion: str) -> str:
    """Add or update a shortcut. Returns confirmation string."""
    shortcuts = _load()
    shortcuts[trigger.lower().strip()] = expansion
    _save(shortcuts)
    return f"Got it. '{trigger}' will now run: {expansion}"

def remove_shortcut(trigger: str) -> str:
    """Remove a shortcut by trigger. Returns confirmation string."""
    shortcuts = _load()
    key = trigger.lower().strip()
    if key in shortcuts:
        del shortcuts[key]
        _save(shortcuts)
        return f"Shortcut '{trigger}' removed."
    return f"No shortcut found for '{trigger}'."

def list_shortcuts() -> str:
    """Returns a formatted list of all shortcuts."""
    shortcuts = _load()
    if not shortcuts:
        return "No shortcuts saved yet."
    lines = ["── Saved Shortcuts ──"]
    for k, v in shortcuts.items():
        lines.append(f"  '{k}'  →  {v}")
    return "\n".join(lines)

def handle_meta_command(text: str):
    """
    Call this before your AI to catch shortcut management commands like:
      'add shortcut open project → open PyCharm at D:/...'
      'list shortcuts'
      'remove shortcut morning'
    Returns (handled: bool, response: str)
    """
    t = text.strip().lower()

    if t in ("list shortcuts", "show shortcuts", "my shortcuts"):
        return True, list_shortcuts()

    m = re.match(r"add shortcut (.+?)\s*[→>]\s*(.+)", text, re.IGNORECASE)
    if m:
        return True, add_shortcut(m.group(1).strip(), m.group(2).strip())

    m = re.match(r"remove shortcut (.+)", text, re.IGNORECASE)
    if m:
        return True, remove_shortcut(m.group(1).strip())

    return False, ""
