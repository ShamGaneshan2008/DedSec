import tkinter as tk
from tkinter import scrolledtext
import threading
import subprocess
import sys
import os
import time
import random

DEDSEC_GREEN = "#00FF41"
DEDSEC_DIM   = "#007A1F"
DEDSEC_DARK  = "#0A0A0A"
DEDSEC_PANEL = "#0D1010"
DEDSEC_ACCENT= "#1AFF6B"
DEDSEC_RED   = "#FF3C3C"
DEDSEC_GRAY  = "#1C1C1C"
FONT_MONO    = ("Courier New", 11)
FONT_LARGE   = ("Courier New", 13, "bold")
FONT_SMALL   = ("Courier New", 9)

BOOT_LINES = [
    "[ DedSec v.A ] Initializing secure shell...",
    "[ MARCUS ] Loading neural core... OK",
    "[ MEMORY ] Reading memory.json... OK",
    "[ VOICE  ] Speech engine standby... OK",
    "[ NET    ] Establishing encrypted channel...",
    "[ AUTH   ] Identity verified. Welcome back.",
    "─" * 52,
    "  MARCUS is online. Type your command below.",
    "─" * 52,
]

GLITCH_CHARS = "!@#$%^&*<>?/|\\█▓▒░"


class DedSecGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("DedSec V.A — MARCUS")
        self.root.configure(bg=DEDSEC_DARK)
        self.root.geometry("820x620")
        self.root.resizable(True, True)
        self.root.minsize(600, 420)

        self._build_titlebar()
        self._build_output()
        self._build_statusbar()
        self._build_input()

        self.glitch_active = False
        self.root.after(200, self._boot_sequence)

    def _build_titlebar(self):
        bar = tk.Frame(self.root, bg=DEDSEC_GRAY, height=34)
        bar.pack(fill=tk.X, side=tk.TOP)
        tk.Label(bar, text="◈ DEDSEC V.A", bg=DEDSEC_GRAY,
                 fg=DEDSEC_GREEN, font=FONT_LARGE, padx=12).pack(side=tk.LEFT, pady=4)
        self.status_dot = tk.Label(bar, text="●", bg=DEDSEC_GRAY, fg=DEDSEC_DIM, font=FONT_SMALL)
        self.status_dot.pack(side=tk.LEFT)
        self.status_lbl = tk.Label(bar, text="OFFLINE", bg=DEDSEC_GRAY, fg=DEDSEC_DIM, font=FONT_SMALL)
        self.status_lbl.pack(side=tk.LEFT, padx=(2, 0))
        tk.Button(bar, text="✕", bg=DEDSEC_GRAY, fg="#888", bd=0, padx=10,
                  font=FONT_SMALL, activebackground="#333",
                  command=self.root.quit).pack(side=tk.RIGHT, pady=4)
        self.glitch_btn = tk.Button(bar, text="≋ GLITCH", bg=DEDSEC_GRAY, fg=DEDSEC_DIM,
                                    bd=0, padx=8, font=FONT_SMALL, activebackground="#333",
                                    command=self._toggle_glitch)
        self.glitch_btn.pack(side=tk.RIGHT, pady=4)
        tk.Button(bar, text="⊘ CLEAR", bg=DEDSEC_GRAY, fg=DEDSEC_DIM,
                  bd=0, padx=8, font=FONT_SMALL, activebackground="#333",
                  command=self._clear).pack(side=tk.RIGHT, pady=4)

    def _build_output(self):
        frame = tk.Frame(self.root, bg=DEDSEC_PANEL,
                         highlightbackground=DEDSEC_DIM, highlightthickness=1)
        frame.pack(fill=tk.BOTH, expand=True, padx=6, pady=(4, 0))
        self.output = scrolledtext.ScrolledText(
            frame, bg=DEDSEC_PANEL, fg=DEDSEC_GREEN, font=FONT_MONO,
            insertbackground=DEDSEC_GREEN, selectbackground=DEDSEC_DIM,
            bd=0, relief=tk.FLAT, wrap=tk.WORD, state=tk.DISABLED,
            padx=10, pady=8, spacing3=2,
        )
        self.output.pack(fill=tk.BOTH, expand=True)
        self.output.tag_config("dim",    foreground=DEDSEC_DIM)
        self.output.tag_config("bright", foreground=DEDSEC_ACCENT)
        self.output.tag_config("user",   foreground="#FFFFFF")
        self.output.tag_config("error",  foreground=DEDSEC_RED)
        self.output.tag_config("system", foreground="#4AF7A0")

    def _build_statusbar(self):
        bar = tk.Frame(self.root, bg=DEDSEC_GRAY, height=20)
        bar.pack(fill=tk.X, side=tk.BOTTOM)
        self.sb_left = tk.Label(bar, text="MARCUS.AI / v1.0", bg=DEDSEC_GRAY,
                                fg=DEDSEC_DIM, font=FONT_SMALL, padx=8)
        self.sb_left.pack(side=tk.LEFT)
        self.sb_right = tk.Label(bar, text="SECURE CHANNEL", bg=DEDSEC_GRAY,
                                 fg=DEDSEC_DIM, font=FONT_SMALL, padx=8)
        self.sb_right.pack(side=tk.RIGHT)
        self.ticker = tk.Label(bar, text="", bg=DEDSEC_GRAY, fg="#2A6640", font=FONT_SMALL)
        self.ticker.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self._animate_ticker()

    def _build_input(self):
        frame = tk.Frame(self.root, bg=DEDSEC_DARK, pady=6)
        frame.pack(fill=tk.X, padx=6, side=tk.BOTTOM)
        tk.Label(frame, text="marcus@dedsec:~$", bg=DEDSEC_DARK,
                 fg=DEDSEC_GREEN, font=FONT_LARGE).pack(side=tk.LEFT, padx=(0, 6))
        self.entry = tk.Entry(frame, bg=DEDSEC_PANEL, fg=DEDSEC_GREEN,
                              insertbackground=DEDSEC_GREEN, font=FONT_LARGE,
                              bd=0, relief=tk.FLAT, highlightthickness=1,
                              highlightbackground=DEDSEC_DIM, highlightcolor=DEDSEC_GREEN)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4)
        self.entry.bind("<Return>", self._send)
        self.entry.focus_set()
        tk.Button(frame, text="▶ SEND", bg=DEDSEC_DIM, fg=DEDSEC_DARK,
                  activebackground=DEDSEC_GREEN, activeforeground=DEDSEC_DARK,
                  font=FONT_SMALL, bd=0, padx=10,
                  command=self._send).pack(side=tk.LEFT, padx=(6, 0), ipady=4)

    def _write(self, text, tag=""):
        self.output.config(state=tk.NORMAL)
        self.output.insert(tk.END, text, tag)
        self.output.see(tk.END)
        self.output.config(state=tk.DISABLED)

    def _clear(self):
        self.output.config(state=tk.NORMAL)
        self.output.delete("1.0", tk.END)
        self.output.config(state=tk.DISABLED)

    def _boot_sequence(self):
        def run():
            for line in BOOT_LINES:
                time.sleep(0.18)
                tag = "dim" if line.startswith("─") else "system"
                self.root.after(0, self._write, line + "\n", tag)
            self.root.after(0, self._set_online)
        threading.Thread(target=run, daemon=True).start()

    def _set_online(self):
        self.status_dot.config(fg=DEDSEC_GREEN)
        self.status_lbl.config(fg=DEDSEC_GREEN, text="ONLINE")

    def _send(self, event=None):
        cmd = self.entry.get().strip()
        if not cmd:
            return
        self.entry.delete(0, tk.END)
        self._write(f"\n> {cmd}\n", "user")
        threading.Thread(target=self._run_marcus, args=(cmd,), daemon=True).start()

    def _run_marcus(self, cmd):
        self.root.after(0, self._write, "[ MARCUS ] Processing...\n", "dim")
        try:
            env = os.environ.copy()
            env["MARCUS_GUI"] = "1"
            result = subprocess.run(
                [sys.executable, "main.py", "--cmd", cmd],
                capture_output=True, text=True, timeout=30,
                cwd=os.path.dirname(os.path.abspath(__file__)),
                env=env,
            )
            response = result.stdout.strip() or result.stderr.strip()
            if not response:
                response = "[No response — check main.py accepts --cmd flag]"
        except subprocess.TimeoutExpired:
            response = "[TIMEOUT] Marcus took too long to respond."
        except Exception as e:
            response = f"[ERROR] {e}"
        tag = "error" if response.startswith("[ERROR]") else "bright"
        self.root.after(0, self._write, f"\n{response}\n\n", tag)

    def _toggle_glitch(self):
        self.glitch_active = not self.glitch_active
        self.glitch_btn.config(fg=DEDSEC_GREEN if self.glitch_active else DEDSEC_DIM)
        if self.glitch_active:
            self._do_glitch()

    def _do_glitch(self):
        if not self.glitch_active:
            return
        glitch = "".join(random.choices(GLITCH_CHARS, k=random.randint(8, 24)))
        self._write(glitch + "\r", "dim")
        self.root.after(random.randint(40, 200), self._do_glitch)

    def _animate_ticker(self):
        msgs = ["ENCRYPTION ACTIVE", "NODE: CHICAGO-03", "PACKET LOSS: 0.00%",
                "UPLINK STABLE", "SIGNAL STRENGTH: MAX", "FIREWALL: ENGAGED"]
        self.ticker.config(text=f"  //  {random.choice(msgs)}  //")
        self.root.after(3000, self._animate_ticker)


def main():
    root = tk.Tk()
    DedSecGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
