"""
Marcus V.A — Modern Chat GUI with Real-Time Subtitles
DedSec V.A  |  gui.py
"""

import tkinter as tk
from tkinter import scrolledtext
import threading
import subprocess
import sys
import os
import time
import random
import math
import re
from datetime import datetime


_HERE = os.path.dirname(os.path.abspath(__file__))
_UI   = os.path.abspath(os.path.join(_HERE, "..", "frontend", "index.html"))

# ──────────────────────────────────────────────
#  THEME
# ──────────────────────────────────────────────
BG_APP      = "#0F0F0F"
BG_SIDEBAR  = "#161616"
BG_CHAT     = "#0F0F0F"
BG_BUBBLE_A = "#1A1A1A"
BG_BUBBLE_U = "#3D3580"
BG_INPUT    = "#1A1A1A"
BG_HEADER   = "#111111"
BG_CODE     = "#141414"

ACCENT      = "#7C6FCD"
ACCENT_HI   = "#9D91E8"
GREEN       = "#1D9E75"
RED         = "#E05C5C"
DIM         = "#555555"
MID         = "#888888"
LIGHT       = "#E8E8E8"
WHITE       = "#FFFFFF"
GOLD        = "#C9A84C"
CODE_FG     = "#A8D8A8"

FONT_UI     = ("Segoe UI",     11)
FONT_MSG    = ("Segoe UI",     12)
FONT_META   = ("Segoe UI",      9)
FONT_TITLE  = ("Segoe UI",     13, "bold")
FONT_SMALL  = ("Segoe UI",      9)
FONT_BTN    = ("Segoe UI",     10)
FONT_MONO   = ("Courier New",  10)
FONT_SUBTITLE = ("Segoe UI",   15)
FONT_H1     = ("Segoe UI",     16, "bold")
FONT_H2     = ("Segoe UI",     14, "bold")
FONT_H3     = ("Segoe UI",     12, "bold")
FONT_BOLD   = ("Segoe UI",     12, "bold")
FONT_ITALIC = ("Segoe UI",     12, "italic")
FONT_CODE   = ("Courier New",  11)

BUBBLE_WIDTH = 68   # chars — adjust if needed

TICKER_MSGS = [
    "ENCRYPTION ACTIVE", "NODE: CHICAGO-03", "PACKET LOSS: 0.00%",
    "UPLINK STABLE", "SIGNAL STRENGTH: MAX", "FIREWALL: ENGAGED",
    "NEURAL LINK: ACTIVE", "GHOST MODE: STANDBY", "DEDSEC NET: SECURE",
    "LATENCY: 2ms", "MEMORY: LOADED", "VOICE ENGINE: READY",
]

BOOT_LINES = [
    ("[ DedSec V.A ]  Initializing secure shell...", "dim"),
    ("[ MARCUS ]  Loading neural core ............. OK", "ok"),
    ("[ MEMORY ]  Reading memory.json ............. OK", "ok"),
    ("[ VOICE  ]  ElevenLabs engine standby ....... OK", "ok"),
    ("[ NET    ]  Establishing encrypted channel .. OK", "ok"),
    ("[ AUTH   ]  Identity verified. Welcome back.", "hi"),
]

GLITCH_CHARS = "!@#$%^&*<>?/|\\█▓▒░"


# ──────────────────────────────────────────────
#  MARKDOWN RENDERER
# ──────────────────────────────────────────────
def _configure_tags(txt: tk.Text, bg: str):
    """Set up all text tags on a Text widget for markdown rendering."""
    txt.tag_config("h1",       font=FONT_H1,     foreground=WHITE,    spacing1=8, spacing3=4)
    txt.tag_config("h2",       font=FONT_H2,     foreground=LIGHT,    spacing1=6, spacing3=3)
    txt.tag_config("h3",       font=FONT_H3,     foreground=LIGHT,    spacing1=4, spacing3=2)
    txt.tag_config("bold",     font=FONT_BOLD,   foreground=WHITE)
    txt.tag_config("italic",   font=FONT_ITALIC, foreground=LIGHT)
    txt.tag_config("code",     font=FONT_CODE,   foreground=CODE_FG,  background="#1E2A1E")
    txt.tag_config("codeblock",font=FONT_CODE,   foreground=CODE_FG,  background=BG_CODE,
                   lmargin1=12, lmargin2=12, spacing1=2, spacing3=2)
    txt.tag_config("bullet",   font=FONT_MSG,    foreground=LIGHT,    lmargin1=8, lmargin2=20)
    txt.tag_config("bullet_dot",font=FONT_MSG,   foreground=ACCENT)
    txt.tag_config("numbered", font=FONT_MSG,    foreground=LIGHT,    lmargin1=8, lmargin2=28)
    txt.tag_config("num_label",font=FONT_BOLD,   foreground=ACCENT_HI)
    txt.tag_config("hr",       font=FONT_SMALL,  foreground=DIM,      spacing1=4, spacing3=4)
    txt.tag_config("normal",   font=FONT_MSG,    foreground=LIGHT)
    txt.tag_config("dim",      font=FONT_MSG,    foreground=DIM)
    txt.tag_config("ok",       font=FONT_MSG,    foreground=GREEN)
    txt.tag_config("hi",       font=FONT_MSG,    foreground=ACCENT_HI)


def _insert_markdown(txt: tk.Text, text: str):
    """Parse and insert markdown-formatted text into a tk.Text widget."""
    lines = text.split("\n")
    in_code = False
    code_buf = []

    def flush_code():
        nonlocal code_buf
        block = "\n".join(code_buf)
        txt.insert(tk.END, block + "\n", "codeblock")
        code_buf = []

    i = 0
    while i < len(lines):
        line = lines[i]

        # ── Code fence ───────────────────────────
        if line.strip().startswith("```"):
            if not in_code:
                in_code = True
                code_buf = []
            else:
                in_code = False
                flush_code()
            i += 1
            continue

        if in_code:
            code_buf.append(line)
            i += 1
            continue

        # ── HR ───────────────────────────────────
        if re.match(r'^[-*_]{3,}\s*$', line):
            txt.insert(tk.END, "─" * 50 + "\n", "hr")
            i += 1
            continue

        # ── Headings ─────────────────────────────
        h3 = re.match(r'^###\s+(.*)', line)
        h2 = re.match(r'^##\s+(.*)', line)
        h1 = re.match(r'^#\s+(.*)', line)
        if h1:
            txt.insert(tk.END, h1.group(1) + "\n", "h1")
            i += 1
            continue
        if h2:
            txt.insert(tk.END, h2.group(1) + "\n", "h2")
            i += 1
            continue
        if h3:
            txt.insert(tk.END, h3.group(1) + "\n", "h3")
            i += 1
            continue

        # ── Bullet list ──────────────────────────
        bullet = re.match(r'^[\-\*\+]\s+(.*)', line)
        if bullet:
            txt.insert(tk.END, "  • ", "bullet_dot")
            _insert_inline(txt, bullet.group(1), "bullet")
            txt.insert(tk.END, "\n")
            i += 1
            continue

        # ── Numbered list ─────────────────────────
        numbered = re.match(r'^(\d+)\.\s+(.*)', line)
        if numbered:
            txt.insert(tk.END, f"  {numbered.group(1)}. ", "num_label")
            _insert_inline(txt, numbered.group(2), "numbered")
            txt.insert(tk.END, "\n")
            i += 1
            continue

        # ── Blank line ───────────────────────────
        if line.strip() == "":
            txt.insert(tk.END, "\n")
            i += 1
            continue

        # ── Normal paragraph line ────────────────
        _insert_inline(txt, line, "normal")
        txt.insert(tk.END, "\n")
        i += 1

    # flush unclosed code block
    if in_code and code_buf:
        flush_code()


def _insert_inline(txt: tk.Text, text: str, base_tag: str):
    """Handle inline markdown: **bold**, *italic*, `code`."""
    # Pattern: **bold**, *italic*, `code`
    pattern = re.compile(r'(\*\*(.+?)\*\*|\*(.+?)\*|`(.+?)`)')
    last = 0
    for m in pattern.finditer(text):
        # text before match
        if m.start() > last:
            txt.insert(tk.END, text[last:m.start()], base_tag)
        if m.group(0).startswith("**"):
            txt.insert(tk.END, m.group(2), "bold")
        elif m.group(0).startswith("*"):
            txt.insert(tk.END, m.group(3), "italic")
        elif m.group(0).startswith("`"):
            txt.insert(tk.END, m.group(4), "code")
        last = m.end()
    if last < len(text):
        txt.insert(tk.END, text[last:], base_tag)


# ──────────────────────────────────────────────
#  SUBTITLE WIDGET
# ──────────────────────────────────────────────
class SubtitleWidget(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=BG_APP, **kwargs)
        self.configure(height=80)

        self.subtitle_container = tk.Frame(self, bg="#1A1A1ACC", padx=20, pady=12)
        self.subtitle_container.pack(fill=tk.BOTH, expand=True, padx=40, pady=10)

        self.subtitle_label = tk.Label(
            self.subtitle_container, text="", bg="#1A1A1A",
            fg=WHITE, font=FONT_SUBTITLE, wraplength=800, justify=tk.CENTER
        )
        self.subtitle_label.pack(expand=True)
        self.pack_forget()

        self._current_text = ""
        self._hide_timer   = None

    def show_subtitle(self, text: str):
        self._current_text = text
        self.subtitle_label.config(text=text)
        if not self.winfo_ismapped():
            self.pack(side=tk.BOTTOM, fill=tk.X, before=self.master.winfo_children()[-2])
        if self._hide_timer:
            self.after_cancel(self._hide_timer)
            self._hide_timer = None

    def append_subtitle(self, token: str):
        self._current_text += token
        self.subtitle_label.config(text=self._current_text)
        if not self.winfo_ismapped():
            self.pack(side=tk.BOTTOM, fill=tk.X, before=self.master.winfo_children()[-2])
        if self._hide_timer:
            self.after_cancel(self._hide_timer)
            self._hide_timer = None

    def clear_subtitle(self, delay_ms: int = 2000):
        if self._hide_timer:
            self.after_cancel(self._hide_timer)
        self._hide_timer = self.after(delay_ms, self._hide_subtitle)

    def _hide_subtitle(self):
        self._current_text = ""
        self.subtitle_label.config(text="")
        self.pack_forget()
        self._hide_timer = None


# ──────────────────────────────────────────────
#  WAVEFORM WIDGET
# ──────────────────────────────────────────────
class WaveformCanvas(tk.Canvas):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._bars    = 32
        self._active  = False
        self._heights = [1.0] * self._bars
        self._targets = [1.0] * self._bars
        self.after(50, self._loop)

    def activate(self):   self._active = True
    def deactivate(self):
        self._active  = False
        self._targets = [1.0] * self._bars

    def _loop(self):
        if self._active:
            cx = self._bars // 2
            for i in range(self._bars):
                dist = abs(i - cx) / cx
                peak = 28 * (1 - dist * 0.55) * random.uniform(0.3, 1.0)
                self._targets[i] = max(1.5, peak)
        for i in range(self._bars):
            self._heights[i] += (self._targets[i] - self._heights[i]) * 0.3
        self._draw()
        self.after(40, self._loop)

    def _draw(self):
        self.delete("all")
        w   = self.winfo_width()  or 400
        h   = self.winfo_height() or 36
        mid = h / 2
        gap = w / self._bars
        bw  = max(1, gap * 0.45)
        for i, bh in enumerate(self._heights):
            x     = i * gap + gap / 2
            ratio = bh / 28
            col   = ACCENT_HI if ratio > 0.6 else (ACCENT if ratio > 0.25 else "#2A2440")
            self.create_rectangle(x-bw, mid-bh, x+bw, mid+bh, fill=col, outline="")


# ──────────────────────────────────────────────
#  MAIN GUI
# ──────────────────────────────────────────────
class MarcusGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Marcus — DedSec V.A")
        self.root.configure(bg=BG_APP)
        self.root.geometry("980x720")
        self.root.minsize(700, 500)
        self.root.resizable(True, True)

        self._streaming      = False
        self._mic_active     = False
        self.glitch_on       = False
        self._msg_widgets    = []
        self._current_bubble = None   # tk.Text being streamed into
        self._stream_buffer  = ""     # raw token buffer for deferred render

        self._build_layout()
        self.root.after(300, self._boot_sequence)

    # ──────────────────────────────────────────
    #  LAYOUT
    # ──────────────────────────────────────────
    def _build_layout(self):
        self.sidebar = tk.Frame(self.root, bg=BG_SIDEBAR, width=220)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)
        self._build_sidebar()

        main = tk.Frame(self.root, bg=BG_APP)
        main.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._build_header(main)
        self._build_chat(main)
        self._build_waveform_bar(main)

        self.subtitle_widget = SubtitleWidget(main)
        self._build_input_bar(main)

    # ── Sidebar ───────────────────────────────
    def _build_sidebar(self):
        sb = self.sidebar

        logo_frame = tk.Frame(sb, bg=BG_SIDEBAR)
        logo_frame.pack(fill=tk.X, padx=16, pady=(20, 8))
        tk.Label(logo_frame, text="◈", bg=BG_SIDEBAR, fg=ACCENT,
                 font=("Segoe UI", 20)).pack(side=tk.LEFT)
        tk.Label(logo_frame, text="  MARCUS", bg=BG_SIDEBAR, fg=LIGHT,
                 font=("Segoe UI", 14, "bold")).pack(side=tk.LEFT)
        tk.Label(sb, text="DedSec V.A", bg=BG_SIDEBAR, fg=DIM,
                 font=FONT_SMALL).pack(anchor="w", padx=20)

        self._sidebar_divider(sb)

        status_card = tk.Frame(sb, bg="#1C1C1C", padx=12, pady=10)
        status_card.pack(fill=tk.X, padx=12, pady=4)
        row = tk.Frame(status_card, bg="#1C1C1C")
        row.pack(fill=tk.X)
        self._dot = tk.Label(row, text="●", bg="#1C1C1C", fg="#333", font=("Segoe UI", 8))
        self._dot.pack(side=tk.LEFT)
        self._status_lbl = tk.Label(row, text="  Offline", bg="#1C1C1C",
                                    fg=DIM, font=FONT_SMALL)
        self._status_lbl.pack(side=tk.LEFT)

        self._sidebar_divider(sb)

        nav_items = [
            ("🗨  New chat",  self._clear_chat),
            ("💾  Memory",    lambda: None),
            ("⌨  Shortcuts", lambda: None),
            ("⚙  Settings",  lambda: None),
        ]
        for label, cmd in nav_items:
            btn = tk.Label(sb, text=label, bg=BG_SIDEBAR, fg=MID,
                           font=FONT_UI, cursor="hand2", anchor="w", padx=20, pady=8)
            btn.pack(fill=tk.X)
            btn.bind("<Button-1>", lambda e, c=cmd: c())
            btn.bind("<Enter>", lambda e, w=btn: w.config(bg="#222", fg=WHITE))
            btn.bind("<Leave>", lambda e, w=btn: w.config(bg=BG_SIDEBAR, fg=MID))

        self._sidebar_divider(sb)

        self.glitch_btn = tk.Label(sb, text="⚡ Glitch mode", bg=BG_SIDEBAR,
                                   fg=DIM, font=FONT_UI, cursor="hand2",
                                   anchor="w", padx=20, pady=8)
        self.glitch_btn.pack(fill=tk.X)
        self.glitch_btn.bind("<Button-1>", lambda e: self._toggle_glitch())

    def _sidebar_divider(self, parent):
        tk.Frame(parent, bg="#282828", height=1).pack(fill=tk.X, padx=12, pady=8)

    # ── Header ────────────────────────────────
    def _build_header(self, parent):
        hdr = tk.Frame(parent, bg=BG_HEADER, height=50)
        hdr.pack(fill=tk.X, side=tk.TOP)
        hdr.pack_propagate(False)

        left = tk.Frame(hdr, bg=BG_HEADER)
        left.pack(side=tk.LEFT, padx=16, pady=8)
        tk.Label(left, text="Marcus", bg=BG_HEADER, fg=WHITE,
                 font=FONT_TITLE).pack(side=tk.LEFT)

        status_row = tk.Frame(left, bg=BG_HEADER)
        status_row.pack(side=tk.LEFT, padx=(12, 0))
        self._hdr_dot = tk.Label(status_row, text="●", bg=BG_HEADER, fg="#333",
                                 font=("Segoe UI", 8))
        self._hdr_dot.pack(side=tk.LEFT)
        self._hdr_status = tk.Label(status_row, text=" Offline", bg=BG_HEADER,
                                    fg=DIM, font=FONT_SMALL)
        self._hdr_status.pack(side=tk.LEFT)

        self.ticker = tk.Label(hdr, text="// INITIALIZING //", bg=BG_HEADER,
                               fg=DIM, font=FONT_MONO)
        self.ticker.pack(side=tk.RIGHT, padx=20)

    # ── Chat area ─────────────────────────────
    def _build_chat(self, parent):
        chat_container = tk.Frame(parent, bg=BG_CHAT)
        chat_container.pack(fill=tk.BOTH, expand=True, side=tk.TOP)

        canvas    = tk.Canvas(chat_container, bg=BG_CHAT, highlightthickness=0)
        scrollbar = tk.Scrollbar(chat_container, orient=tk.VERTICAL, command=canvas.yview)
        self.chat_frame = tk.Frame(canvas, bg=BG_CHAT)

        self.chat_frame.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.chat_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_canvas = canvas

    def _scroll_bottom(self):
        self.chat_canvas.update_idletasks()
        self.chat_canvas.yview_moveto(1.0)

    # ── Waveform ──────────────────────────────
    def _build_waveform_bar(self, parent):
        wf_frame = tk.Frame(parent, bg=BG_APP, height=50)
        wf_frame.pack(fill=tk.X, side=tk.TOP)
        wf_frame.pack_propagate(False)
        self.waveform = WaveformCanvas(wf_frame, bg=BG_APP, highlightthickness=0, height=36)
        self.waveform.pack(fill=tk.BOTH, expand=True, padx=20, pady=6)

    # ── Input bar ─────────────────────────────
    def _build_input_bar(self, parent):
        bar = tk.Frame(parent, bg=BG_INPUT, height=60)
        bar.pack(fill=tk.X, side=tk.BOTTOM)
        bar.pack_propagate(False)

        inner = tk.Frame(bar, bg=BG_INPUT)
        inner.pack(fill=tk.BOTH, expand=True, padx=16, pady=10)

        self.mic_btn = tk.Label(inner, text="🎙", bg=BG_INPUT, fg=DIM,
                                font=("Segoe UI", 16), cursor="hand2")
        self.mic_btn.pack(side=tk.LEFT, padx=(0, 8))
        self.mic_btn.bind("<Button-1>", lambda e: self._toggle_mic())

        self.entry = tk.Entry(inner, bg="#222", fg=WHITE, font=FONT_MSG,
                              insertbackground=WHITE, relief=tk.FLAT, bd=0)
        self.entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, ipady=6, padx=8)
        self.entry.bind("<Return>", self._send)

        self.send_btn = tk.Label(inner, text="➤", bg=ACCENT, fg=WHITE,
                                 font=("Segoe UI", 14, "bold"),
                                 cursor="hand2", padx=12, pady=4)
        self.send_btn.pack(side=tk.RIGHT)
        self.send_btn.bind("<Button-1>", self._send)

    # ──────────────────────────────────────────
    #  CHAT BUBBLES
    # ──────────────────────────────────────────
    def _add_bubble(self, text: str, sender: str, render_markdown: bool = False):
        """
        Creates a chat bubble. Returns the inner tk.Text widget.
        render_markdown=True parses the text as markdown before inserting.
        """
        is_user = (sender == "user")
        align   = tk.E if is_user else tk.W
        bg      = BG_BUBBLE_U if is_user else BG_BUBBLE_A

        bubble_frame = tk.Frame(self.chat_frame, bg=BG_CHAT)
        bubble_frame.pack(fill=tk.X, padx=20, pady=(4, 2))

        inner = tk.Frame(bubble_frame, bg=BG_CHAT)
        inner.pack(anchor=align)

        # ── Avatar row ───────────────────────
        meta_row = tk.Frame(inner, bg=BG_CHAT)
        meta_row.pack(anchor=align, pady=(0, 3))

        if is_user:
            tk.Label(meta_row, text="You", bg=BG_CHAT, fg=MID,
                     font=FONT_META).pack(side=tk.RIGHT, padx=(0, 6))
            tk.Label(meta_row, text="👤", bg=BG_CHAT,
                     font=("Segoe UI", 10)).pack(side=tk.RIGHT)
        else:
            tk.Label(meta_row, text="◈", bg=BG_CHAT, fg=ACCENT,
                     font=("Segoe UI", 10)).pack(side=tk.LEFT)
            tk.Label(meta_row, text=" Marcus", bg=BG_CHAT, fg=MID,
                     font=FONT_META).pack(side=tk.LEFT)

        # ── Bubble body ──────────────────────
        bubble_bg = tk.Frame(inner, bg=bg, padx=14, pady=10)
        bubble_bg.pack(anchor=align)

        # Left accent bar for Marcus bubbles
        if not is_user:
            accent_bar = tk.Frame(bubble_bg, bg=ACCENT, width=3)
            accent_bar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        txt = tk.Text(
            bubble_bg, bg=bg, fg=LIGHT, font=FONT_MSG,
            wrap=tk.WORD, relief=tk.FLAT, bd=0,
            highlightthickness=0, state=tk.DISABLED,
            cursor="arrow", width=BUBBLE_WIDTH,
            spacing1=2, spacing2=2, spacing3=2,
            padx=4, pady=4,
        )
        txt.pack(side=tk.LEFT)

        _configure_tags(txt, bg)

        txt.config(state=tk.NORMAL)
        if text:
            if render_markdown and not is_user:
                _insert_markdown(txt, text)
            else:
                txt.insert(tk.END, text)
        txt.config(state=tk.DISABLED)

        self._resize_bubble_text(txt)
        self._msg_widgets.append((bubble_frame, txt))
        self._scroll_bottom()
        return txt

    def _resize_bubble_text(self, txt_widget):
        txt_widget.update_idletasks()
        line_count = int(txt_widget.index("end-1c").split(".")[0])
        txt_widget.config(height=max(1, line_count))

    # ──────────────────────────────────────────
    #  STREAMING BUBBLE
    # ──────────────────────────────────────────
    def _start_stream_bubble(self):
        self._stream_buffer  = ""
        self._current_bubble = self._add_bubble("", "marcus", render_markdown=False)
        self._streaming      = True
        self.waveform.activate()
        self.subtitle_widget.show_subtitle("")

    def _stream_chunk(self, chunk: str, tag: str = ""):
        """Append raw token to buffer and re-render the bubble with markdown."""
        if self._current_bubble is None:
            return

        txt = self._current_bubble

        if tag in ("ok", "hi", "dim"):
            # Boot sequence — plain tagged text, no markdown
            txt.config(state=tk.NORMAL)
            txt.tag_config(tag, foreground={"ok": GREEN, "hi": ACCENT_HI, "dim": DIM}[tag])
            txt.insert(tk.END, chunk, tag)
            txt.config(state=tk.DISABLED)
        else:
            # Normal streaming: accumulate then re-render markdown
            self._stream_buffer += chunk
            txt.config(state=tk.NORMAL)
            txt.delete("1.0", tk.END)
            _insert_markdown(txt, self._stream_buffer)
            txt.config(state=tk.DISABLED)
            if not tag:
                self.subtitle_widget.append_subtitle(chunk)

        self._resize_bubble_text(txt)
        self._scroll_bottom()

    def _end_stream_bubble(self):
        self._current_bubble = None
        self._streaming      = False
        self._stream_buffer  = ""
        self.waveform.deactivate()
        self.send_btn.config(bg=ACCENT, fg=WHITE)
        self.subtitle_widget.clear_subtitle(delay_ms=2000)

    # ──────────────────────────────────────────
    #  SEND / STREAM
    # ──────────────────────────────────────────
    def _send(self, event=None):
        if self._streaming:
            return
        cmd = self.entry.get().strip()
        if not cmd:
            return
        self.entry.delete(0, tk.END)
        self._add_bubble(cmd, "user")
        threading.Thread(target=self._stream_marcus, args=(cmd,), daemon=True).start()

    def _stream_marcus(self, cmd: str):
        self._streaming = True
        self.root.after(0, lambda: self.send_btn.config(bg="#2A2A2A", fg=DIM))
        self.root.after(0, self._start_stream_bubble)

        try:
            import os
            if getattr(sys, 'frozen', False):
                root_dir = os.path.dirname(sys.executable)
            else:
                root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

            from dotenv import load_dotenv
            env_locations = [
                os.path.join(root_dir, 'backend', '../.env'),
                os.path.join(root_dir, '../.env'),
                os.path.join(os.path.dirname(sys.executable), '_internal', 'backend', '../.env'),
                os.path.join(os.getcwd(), 'backend', '../.env'),
            ]
            for env_path in env_locations:
                if os.path.exists(env_path):
                    load_dotenv(env_path, override=True)
                    break

            from backend.marcus.core.memory import Memory
            from backend.marcus.core.ai import AI
            from backend.marcus.core.router import Router

            memory = Memory()
            ai     = AI(memory=memory)
            router = Router(ai=ai, memory=memory)
            result = router.handle_stream(cmd)

            if hasattr(result, '__iter__') and not isinstance(result, str):
                for token in result:
                    if token:
                        self.root.after(0, self._stream_chunk, token)
            else:
                self.root.after(0, self._stream_chunk, str(result))

        except Exception as e:
            self.root.after(0, self._stream_chunk, f"[ERROR] {e}")
        finally:
            self.root.after(0, self._end_stream_bubble)

    # ──────────────────────────────────────────
    #  MIC
    # ──────────────────────────────────────────
    def _toggle_mic(self):
        if self._mic_active:
            self._stop_mic()
        else:
            self._start_mic()

    def _start_mic(self):
        self._mic_active = True
        self.mic_btn.config(fg=RED)
        self._add_bubble("🎙 Listening…", "user")
        threading.Thread(target=self._mic_listen, daemon=True).start()

    def _stop_mic(self):
        self._mic_active = False
        self.mic_btn.config(fg=DIM)

    def _mic_listen(self):
        try:
            import speech_recognition as sr
            r = sr.Recognizer()
            r.energy_threshold         = 400
            r.dynamic_energy_threshold = False
            with sr.Microphone(device_index=2) as source:
                r.adjust_for_ambient_noise(source, duration=0.5)
                audio = r.listen(source, timeout=6, phrase_time_limit=15)

            try:
                import io, wave
                from groq import Groq
                from dotenv import load_dotenv
                load_dotenv()
                client = Groq(api_key=os.getenv("GROQ_API_KEY"))
                buf = io.BytesIO()
                with wave.open(buf, "wb") as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(audio.sample_width)
                    wf.setframerate(audio.sample_rate)
                    wf.writeframes(audio.get_raw_data())
                buf.seek(0)
                buf.name = "audio.wav"
                result = client.audio.transcriptions.create(
                    model="whisper-large-v3-turbo",
                    file=buf, language="en", response_format="text"
                )
                text = result.strip() if isinstance(result, str) else result.text.strip()
            except Exception:
                text = r.recognize_google(audio)

            if text:
                self.root.after(0, self.entry.delete, 0, tk.END)
                self.root.after(0, self.entry.insert, 0, text)
                self.root.after(0, self._send)
            else:
                self.root.after(0, lambda: self._add_bubble("Didn't catch that. Try again.", "marcus"))

        except Exception as e:
            self.root.after(0, lambda: self._add_bubble(f"Mic error: {e}", "marcus"))
        finally:
            self._mic_active = False
            self.root.after(0, self.mic_btn.config, {"fg": DIM})

    # ──────────────────────────────────────────
    #  STATUS / ONLINE
    # ──────────────────────────────────────────
    def _set_online(self):
        self._dot.config(fg=GREEN)
        self._status_lbl.config(fg=GREEN, text="  Online")
        self._hdr_dot.config(fg=GREEN)
        self._hdr_status.config(fg=GREEN, text=" Online")
        self.root.after(500, self._animate_ticker)

    # ──────────────────────────────────────────
    #  STREAMING BUBBLE — BOOT
    # ──────────────────────────────────────────
    def _boot_sequence(self):
        def run():
            self.root.after(0, self._start_stream_bubble)
            for line, tag in BOOT_LINES:
                self.root.after(0, self._stream_chunk, line + "\n", tag)
                time.sleep(0.3)
            self.root.after(0, self._end_stream_bubble)
            self.root.after(0, self._set_online)
            time.sleep(0.4)
            greeting = (
                "Hey — I'm **Marcus**, your DedSec V.A.\n\n"
                "Type below or tap 🎙 to talk.\n\n"
                "How can I help?"
            )
            self.root.after(0, lambda: self._add_bubble(greeting, "marcus", render_markdown=True))
        threading.Thread(target=run, daemon=True).start()

    # ──────────────────────────────────────────
    #  CLEAR / GLITCH / TICKER
    # ──────────────────────────────────────────
    def _clear_chat(self):
        for w in self.chat_frame.winfo_children():
            w.destroy()

    def _toggle_glitch(self):
        self.glitch_on = not self.glitch_on
        self.glitch_btn.config(fg=ACCENT if self.glitch_on else DIM)
        if self.glitch_on:
            self._do_glitch()

    def _do_glitch(self):
        if not self.glitch_on:
            return
        g = "".join(random.choices(GLITCH_CHARS, k=random.randint(4, 14)))
        self._add_bubble(g, "marcus")
        self.root.after(random.randint(60, 200), self._do_glitch)

    def _animate_ticker(self):
        self.ticker.config(text=f"// {random.choice(TICKER_MSGS)} //")
        self.root.after(3500, self._animate_ticker)


# ──────────────────────────────────────────────
#  ENTRY POINT
# ──────────────────────────────────────────────
def main():
    root = tk.Tk()
    root.withdraw()
    app = MarcusGUI(root)
    root.deiconify()
    root.mainloop()

if __name__ == "__main__":
    main()