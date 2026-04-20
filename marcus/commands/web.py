import webbrowser
from marcus.commands.base import BaseCommand


class OpenGoogle(BaseCommand):
    name = "open_google"
    triggers = ["open google"]

    def execute(self, command: str) -> str:
        webbrowser.open("https://www.google.com")
        return "Opening Google."


class OpenYouTube(BaseCommand):
    name = "open_youtube"
    triggers = ["open youtube"]

    def execute(self, command: str) -> str:
        webbrowser.open("https://www.youtube.com")
        return "Opening YouTube."


class SearchGoogle(BaseCommand):
    name = "search_google"
    triggers = ["search"]

    def execute(self, command: str) -> str:
        query = command.replace("search", "").strip()
        if not query:
            return "What do you want me to search?"
        url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        webbrowser.open(url)
        return f"Searching for {query}."


class OpenWebsite(BaseCommand):
    name = "open_website"
    triggers = ["open website", "go to", "visit"]

    def execute(self, command: str) -> str:
        for trigger in self.triggers:
            command = command.replace(trigger, "").strip()
        if not command.startswith("http"):
            command = "https://" + command
        webbrowser.open(command)
        return f"Opening {command}."


# ── Exported instances ──────────────────────────────
def open_google():        return OpenGoogle().execute("")
def open_youtube():       return OpenYouTube().execute("")
def search_google(query): return SearchGoogle().execute(f"search {query}")
def open_website(cmd):    return OpenWebsite().execute(cmd)