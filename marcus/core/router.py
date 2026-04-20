from marcus.commands import files, system, web
from marcus.commands import extras

class Router:
    def __init__(self, ai, memory, speech=None):
        self.ai = ai
        self.memory = memory
        self.speech = speech  # passed so timer can speak when it fires

    def handle(self, text: str) -> str:
        lower = text.lower()

        # --- Extra commands (weather, timer, joke, spotify, battery, screenshot) ---
        result = extras.handle(text, speech=self.speech)
        if result is not None:
            return result

        # --- File commands ---
        if any(k in lower for k in ["open file", "read file", "list files", "show files"]):
            return files.handle(text)

        # --- System commands ---
        if any(k in lower for k in ["shutdown", "restart", "volume"]):
            return system.handle(text)

        # --- Web commands ---
        if any(k in lower for k in ["search", "look up", "google", "what is", "who is", "news"]):
            return web.handle(text)

        # --- Memory commands ---
        if any(k in lower for k in ["clear memory", "wipe memory", "forget everything"]):
            self.memory.clear()
            return "Memory wiped clean. Like it never happened."

        # --- Default: AI ---
        return self.ai.chat(text)
