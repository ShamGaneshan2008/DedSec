from marcus.commands import system, web, files
from marcus.core.ai import ask_ai
from marcus.core.memory import save_exchange


def route_command(command: str) -> str:
    cmd = command.lower()

    # =========================
    # 🖥️ SYSTEM COMMANDS
    # =========================
    if "open notepad" in cmd:
        return system.open_notepad()

    elif "shutdown" in cmd:
        return system.shutdown()

    elif "restart" in cmd:
        return system.restart()

    elif "open " in cmd and any(x in cmd for x in ["app", "program"]):
        return system.open_app(cmd)

    # =========================
    # 🌐 WEB COMMANDS
    # =========================
    elif "open google" in cmd:
        return web.open_google()

    elif "open youtube" in cmd:
        return web.open_youtube()

    elif "search" in cmd:
        query = cmd.replace("search", "").strip()
        return web.search_google(query)

    elif any(x in cmd for x in ["go to", "visit", "open website"]):
        return web.open_website(cmd)

    # =========================
    # 📁 FILE COMMANDS
    # =========================
    elif "list files" in cmd:
        return files.list_files()

    elif "open file" in cmd:
        return files.open_file(cmd)

    elif "delete file" in cmd:
        return files.delete_file(cmd)

    elif any(x in cmd for x in ["create file", "make file"]):
        return files.create_file(cmd)

    # =========================
    # 🧠 MEMORY COMMANDS
    # =========================
    elif "clear memory" in cmd:
        from marcus.core.memory import clear_memory
        return clear_memory()

    # =========================
    # 🤖 AI FALLBACK
    # =========================
    else:
        response = ask_ai(command)
        save_exchange(command, response)
        return response