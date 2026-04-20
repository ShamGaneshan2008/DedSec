import os
import time
import random
import subprocess
import threading
import platform
import webbrowser

# ─────────────────────────────────────────────
# WEATHER
# ─────────────────────────────────────────────
def handle_weather(text: str) -> str:
    """Uses wttr.in (no API key needed) to get weather."""
    try:
        import urllib.request
        # Try to extract city from text
        city = "auto"
        for trigger in ["weather in", "weather for", "weather at"]:
            if trigger in text.lower():
                city = text.lower().split(trigger, 1)[-1].strip().split()[0]
                break

        url = f"https://wttr.in/{city}?format=3"
        with urllib.request.urlopen(url, timeout=5) as r:
            result = r.read().decode("utf-8").strip()
        return f"Jacking into weather grid... {result}"
    except Exception as e:
        return f"Weather sensors offline. Can't reach the grid right now."


# ─────────────────────────────────────────────
# TIMER / ALARM
# ─────────────────────────────────────────────
_timer_thread = None

def handle_timer(text: str, speech=None) -> str:
    """Set a countdown timer. E.g. 'set timer for 5 minutes'"""
    import re
    lower = text.lower()

    # Extract number and unit
    match = re.search(r"(\d+)\s*(second|minute|hour|sec|min|hr)s?", lower)
    if not match:
        return "Specify a duration, operative. Like 'set timer for 5 minutes'."

    amount = int(match.group(1))
    unit = match.group(2)

    if unit in ("second", "sec"):
        seconds = amount
        label = f"{amount} second{'s' if amount > 1 else ''}"
    elif unit in ("minute", "min"):
        seconds = amount * 60
        label = f"{amount} minute{'s' if amount > 1 else ''}"
    elif unit in ("hour", "hr"):
        seconds = amount * 3600
        label = f"{amount} hour{'s' if amount > 1 else ''}"
    else:
        return "Couldn't parse that duration."

    def _countdown():
        time.sleep(seconds)
        msg = f"Timer's up, operative. {label} on the clock — time to move."
        print(f"\n[MARCUS] ⏰ {msg}")
        if speech:
            speech.speak(msg)

    global _timer_thread
    _timer_thread = threading.Thread(target=_countdown, daemon=True)
    _timer_thread.start()

    return f"Timer set for {label}. I'll ping you when it's up."


# ─────────────────────────────────────────────
# JOKES
# ─────────────────────────────────────────────
DEDSEC_JOKES = [
    "Why do hackers prefer dark mode? Because light attracts bugs.",
    "I tried to hack the Pentagon once. They said 'access denied'. I said 'challenge accepted'.",
    "Why did the programmer quit? Because they didn't get arrays.",
    "How many hackers does it take to change a lightbulb? None — they just exploit the darkness.",
    "My Wi-Fi password is 'incorrect'. So when people ask, I say the password is 'incorrect'. Works every time.",
    "A SQL query walks into a bar, walks up to two tables and asks... 'Can I join you?'",
    "Why do Java developers wear glasses? Because they don't C#.",
    "I asked Blume Corp for my data. They said it's for my own protection. I said that's exactly what a villain would say.",
    "There are 10 types of people in the world: those who understand binary and those who don't.",
    "Why did the hacker cross the road? To get to the other network.",
]

def handle_joke() -> str:
    return random.choice(DEDSEC_JOKES)


# ─────────────────────────────────────────────
# SPOTIFY
# ─────────────────────────────────────────────
def handle_spotify(text: str) -> str:
    lower = text.lower()
    system = platform.system()

    # Try to open Spotify app first
    try:
        if system == "Windows":
            subprocess.Popen(["start", "spotify:"], shell=True)
        elif system == "Darwin":
            subprocess.Popen(["open", "-a", "Spotify"])
        elif system == "Linux":
            subprocess.Popen(["spotify"])

        if "pause" in lower or "stop" in lower:
            return "Spotify pause — use media keys or the app, operative."
        if "next" in lower or "skip" in lower:
            return "Spotify opened. Hit next track manually or via media keys."
        return "Launching Spotify. Jack in and vibe."
    except Exception:
        # Fallback: open web player
        webbrowser.open("https://open.spotify.com")
        return "Spotify app not found. Opened web player instead."


# ─────────────────────────────────────────────
# BATTERY
# ─────────────────────────────────────────────
def handle_battery() -> str:
    try:
        import psutil
        battery = psutil.sensors_battery()
        if battery is None:
            return "No battery detected. You're hardwired to the grid."
        pct = battery.percent
        plugged = battery.power_plugged
        status = "plugged in and charging" if plugged else "running on battery"
        warning = " Low power warning — find a socket, operative." if pct < 20 and not plugged else ""
        return f"Battery at {pct:.0f}%, {status}.{warning}"
    except ImportError:
        return "psutil not installed. Run: pip install psutil"
    except Exception as e:
        return f"Can't read battery: {e}"


# ─────────────────────────────────────────────
# SCREENSHOT
# ─────────────────────────────────────────────
def handle_screenshot() -> str:
    try:
        import pyautogui
        from datetime import datetime
        filename = f"marcus_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        path = os.path.join(os.path.expanduser("~"), "Desktop", filename)
        pyautogui.screenshot(path)
        return f"Screenshot captured. Saved to desktop as {filename}."
    except ImportError:
        return "pyautogui not installed. Run: pip install pyautogui"
    except Exception as e:
        return f"Screenshot failed: {e}"


# ─────────────────────────────────────────────
# UNIFIED HANDLER
# ─────────────────────────────────────────────
def handle(text: str, speech=None) -> str | None:
    """Returns a response string if command matched, else None."""
    lower = text.lower()

    if any(k in lower for k in ["weather"]):
        return handle_weather(text)

    if any(k in lower for k in ["timer", "alarm", "remind me in", "set a timer"]):
        return handle_timer(text, speech)

    if any(k in lower for k in ["joke", "make me laugh", "say something funny", "tell me a joke"]):
        return handle_joke()

    if any(k in lower for k in ["spotify", "play music", "open music", "music"]):
        return handle_spotify(text)

    if any(k in lower for k in ["battery", "power level", "charge"]):
        return handle_battery()

    if any(k in lower for k in ["screenshot", "capture screen", "take a screenshot"]):
        return handle_screenshot()

    return None  # No match — let router fall through to AI
