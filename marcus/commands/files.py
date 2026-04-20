import os
import subprocess
import platform
from marcus.commands.base import BaseCommand


class ListFiles(BaseCommand):
    name = "list_files"
    triggers = ["list files"]

    def execute(self, command: str) -> str:
        files = os.listdir(".")
        if not files:
            return "No files found in current directory."
        return "Files here: " + ", ".join(files)


class OpenFile(BaseCommand):
    name = "open_file"
    triggers = ["open file"]

    def execute(self, command: str) -> str:
        filename = command.replace("open file", "").strip()
        if not filename:
            return "Which file should I open?"
        if not os.path.exists(filename):
            return f"File '{filename}' not found."
        if platform.system() == "Windows":
            os.startfile(filename)
        elif platform.system() == "Darwin":
            subprocess.call(["open", filename])
        else:
            subprocess.call(["xdg-open", filename])
        return f"Opening {filename}."


class DeleteFile(BaseCommand):
    name = "delete_file"
    triggers = ["delete file"]

    def execute(self, command: str) -> str:
        filename = command.replace("delete file", "").strip()
        if not filename:
            return "Which file should I delete?"
        if not os.path.exists(filename):
            return f"File '{filename}' not found."
        os.remove(filename)
        return f"Deleted {filename}."


class CreateFile(BaseCommand):
    name = "create_file"
    triggers = ["create file", "make file"]

    def execute(self, command: str) -> str:
        for trigger in self.triggers:
            command = command.replace(trigger, "").strip()
        if not command:
            return "What should I name the file?"
        with open(command, "w") as f:
            f.write("")
        return f"Created file: {command}."


# ── Exported instances ──────────────────────────────
def list_files():         return ListFiles().execute("")
def open_file(cmd):       return OpenFile().execute(cmd)
def delete_file(cmd):     return DeleteFile().execute(cmd)
def create_file(cmd):     return CreateFile().execute(cmd)