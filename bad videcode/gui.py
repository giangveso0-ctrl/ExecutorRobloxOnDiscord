#!/usr/bin/env python3
"""
RobloxOnDiscord - Control Panel (GUI)
-------------------------------------
A modern dark desktop window that starts / stops bot.py, keeps your bot token
and shows the live console with colour badges and filters.

Pure standard library (tkinter). psutil is optional (Roblox status light only).

Run:  python gui.py      (or double-click start_gui.bat)
"""
import datetime
import math
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox
from tkinter import font as tkfont

try:
    import psutil
except ImportError:
    psutil = None

# crisp text on high-DPI Windows screens
if os.name == "nt":
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

APP_DIR = Path(__file__).resolve().parent
BOT_FILE = APP_DIR / "bot.py"
TOKEN_FILE = APP_DIR / "token.txt"
DEV_PORTAL = "https://discord.com/developers/applications"
DEFAULT_LOADSTRING_URL = (
    "https://raw.githubusercontent.com/giangveso0-ctrl/ExecutorRobloxOnDiscord/main/bridge.lua"
)

# ------------------------------------------------------------------ theme
BG = "#0e0f14"
CARD = "#161821"
CARD_2 = "#1d2030"
BORDER = "#2a2e42"
FG = "#e6e8f2"
MUTED = "#8a8fa8"
ACCENT = "#7c5cff"
ACCENT_2 = "#3b82f6"
ACCENT_HOVER = "#6a49f0"
GREEN = "#2ecc71"
GREEN_HOVER = "#25a85b"
RED = "#ff5d6c"
RED_HOVER = "#e04858"
YELLOW = "#f5b942"
CYAN = "#4cc9f0"
MAGENTA = "#c792ea"
GHOST = "#232638"
GHOST_HOVER = "#2e3248"
DISABLED = "#22253a"

# Terminal-style monospace look. The first font that is installed gets used.
FONT_CHOICES = ("Cascadia Mono", "Cascadia Code", "JetBrains Mono", "Fira Code",
                "Consolas", "SF Mono", "Menlo", "DejaVu Sans Mono", "Courier New")
UI = "Consolas"
MONO = "Consolas"

LABEL_COLOURS = {
    "OK": GREEN, "INFO": CYAN, "WARN": YELLOW, "ERROR": RED,
    "ROBLOX": MAGENTA, "CONN": GREEN, "DISC": RED,
}
FILTERS = {
    "All": None,
    "Activity": {"OK", "CONN", "DISC", "ROBLOX"},
    "Warnings": {"WARN"},
    "Errors": {"ERROR"},
}

ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
LOG_LINE_RE = re.compile(r"^(\d{2}:\d{2}:\d{2})\s+\[\s*([A-Za-z]+)\s*\]\s?(.*)$")
TOTAL_RE = re.compile(r"Total active:\s*(\d+)")


# ---------------------------------------------------------------- helpers
def hex_to_rgb(colour: str):
    colour = colour.lstrip("#")
    return tuple(int(colour[i:i + 2], 16) for i in (0, 2, 4))


def blend(c1: str, c2: str, t: float) -> str:
    a, b = hex_to_rgb(c1), hex_to_rgb(c2)
    return "#%02x%02x%02x" % tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def round_rect(canvas: tk.Canvas, x1, y1, x2, y2, r, **kw):
    pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
           x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
    return canvas.create_polygon(pts, smooth=True, **kw)


def looks_like_token(token: str) -> bool:
    return token.count(".") == 2 and len(token) >= 50 and " " not in token


def read_bot_constant(name: str, pattern: str, default: str) -> str:
    try:
        text = BOT_FILE.read_text(encoding="utf-8")
        m = re.search(rf'{name}\s*=\s*{pattern}', text)
        if m:
            return m.group(1)
    except OSError:
        pass
    return default


def read_loadstring_url() -> str:
    return read_bot_constant("GITHUB_RAW_SCRIPT", r'"([^"]+)"', DEFAULT_LOADSTRING_URL)


def python_executable() -> str:
    exe = sys.executable
    if exe.lower().endswith("pythonw.exe"):
        cand = exe[:-len("pythonw.exe")] + "python.exe"
        if os.path.isfile(cand):
            return cand
    return exe or shutil.which("python") or "python"


def load_saved_token() -> str:
    env = os.environ.get("DISCORD_BOT_TOKEN", "").strip()
    if env and "TOKEN_HERE" not in env:
        return env
    try:
        return TOKEN_FILE.read_text(encoding="utf-8-sig").strip().strip("\"'")
    except OSError:
        return ""


def open_folder(path: Path) -> None:
    try:
        if os.name == "nt":
            os.startfile(str(path))  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])
    except Exception as exc:
        messagebox.showerror("Open folder", str(exc))


def fmt_duration(seconds: float) -> str:
    seconds = int(seconds)
    h, rest = divmod(seconds, 3600)
    m, s = divmod(rest, 60)
    return f"{h}:{m:02d}:{s:02d}"


# ---------------------------------------------------------------- widgets
class RoundedButton(tk.Canvas):
    """Flat rounded button with hover / pressed / disabled states."""

    def __init__(self, master, text, command, bg=ACCENT, hover=ACCENT_HOVER, fg="#ffffff",
                 parent_bg=CARD, padx=18, height=38, radius=10, font=None, min_width=0):
        self._font = font or tkfont.Font(family=UI, size=10, weight="bold")
        width = max(min_width, self._font.measure(text) + padx * 2)
        super().__init__(master, width=width, height=height, bg=parent_bg,
                         highlightthickness=0, bd=0, cursor="hand2")
        self.text, self.command = text, command
        self.base, self.hover, self.fg = bg, hover, fg
        self.radius, self.w, self.h = radius, width, height
        self.enabled, self._over, self._down = True, False, False
        self.bind("<Enter>", lambda e: self._set_over(True))
        self.bind("<Leave>", lambda e: self._set_over(False))
        self.bind("<ButtonPress-1>", self._press)
        self.bind("<ButtonRelease-1>", self._release)
        self._draw()

    def _colour(self) -> str:
        if not self.enabled:
            return DISABLED
        if self._down:
            return blend(self.hover, "#000000", 0.15)
        return self.hover if self._over else self.base

    def _draw(self) -> None:
        self.delete("all")
        round_rect(self, 1, 1, self.w - 1, self.h - 1, self.radius, fill=self._colour(), outline="")
        self.create_text(self.w / 2, self.h / 2, text=self.text, font=self._font,
                         fill=self.fg if self.enabled else MUTED)

    def _set_over(self, value: bool) -> None:
        self._over = value
        self.config(cursor="hand2" if self.enabled else "arrow")
        self._draw()

    def _press(self, _e) -> None:
        if self.enabled:
            self._down = True
            self._draw()

    def _release(self, e) -> None:
        was_down, self._down = self._down, False
        self._draw()
        if was_down and self.enabled and 0 <= e.x <= self.w and 0 <= e.y <= self.h:
            self.command()

    def set_enabled(self, value: bool) -> None:
        if value != self.enabled:
            self.enabled = value
            self._draw()


class Card(tk.Frame):
    """Rounded card. Put children in `card.body`."""

    def __init__(self, master, outer=BG, fill=CARD, border=BORDER, radius=16, pad=16):
        super().__init__(master, bg=outer)
        self._fill, self._border, self._radius, self._outer = fill, border, radius, outer
        self.bg_canvas = tk.Canvas(self, bg=outer, highlightthickness=0, bd=0)
        self.bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self.body = tk.Frame(self, bg=fill)
        self.body.pack(fill="both", expand=True, padx=pad, pady=pad)
        self.bg_canvas.bind("<Configure>", self._redraw)

    def _redraw(self, e) -> None:
        c = self.bg_canvas
        c.delete("all")
        round_rect(c, 1, 1, e.width - 1, e.height - 1, self._radius,
                   fill=self._fill, outline=self._border)


class Banner(tk.Canvas):
    """Gradient header with logo, title and a live/idle badge."""

    def __init__(self, master):
        super().__init__(master, height=92, bg=BG, highlightthickness=0, bd=0)
        self.live = False
        self.bind("<Configure>", lambda e: self.redraw())

    def set_live(self, live: bool) -> None:
        if live != self.live:
            self.live = live
            self.redraw()

    def redraw(self) -> None:
        w, h = max(self.winfo_width(), 2), 92
        self.delete("all")
        step = 4
        for x in range(0, w, step):
            self.create_rectangle(x, 0, x + step, h, fill=blend(ACCENT, ACCENT_2, x / w), outline="")
        # soft decorative circles
        self.create_oval(w - 190, -70, w - 30, 90, fill=blend(ACCENT_2, "#ffffff", 0.14), outline="")
        self.create_oval(w - 120, 20, w + 40, 180, fill=blend(ACCENT_2, "#ffffff", 0.08), outline="")
        # round the outer corners by painting the background colour over them
        for (cx, cy, sx, sy) in ((0, 0, 1, 1), (w, 0, -1, 1), (0, h, 1, -1), (w, h, -1, -1)):
            r = 16
            pts = [cx, cy, cx + sx * r, cy]
            for i in range(0, 91, 10):
                a = math.radians(i)
                pts += [cx + sx * r * (1 - math.sin(a)), cy + sy * r * (1 - math.cos(a))]
            pts += [cx, cy + sy * r]
            self.create_polygon(pts, fill=BG, outline="")
        self.create_text(28, 36, anchor="w", text="⚡  ExecutorOnDiscord", fill="#ffffff",
                         font=(UI, 20, "bold"))
        self.create_text(30, 66, anchor="w", text="Roblox  ⇄  Discord bridge  ·  Control Panel",
                         fill=blend("#ffffff", ACCENT, 0.25), font=(UI, 10))
        label = "●  LIVE" if self.live else "○  IDLE"
        bx2, bx1 = w - 24, w - 24 - 96
        round_rect(self, bx1, 30, bx2, 62, 16, fill=blend("#000000", ACCENT, 0.35), outline="")
        self.create_text((bx1 + bx2) / 2, 46, text=label, font=(UI, 10, "bold"),
                         fill=GREEN if self.live else blend("#ffffff", ACCENT, 0.4))


class StatusCard(Card):
    """Title, big value, subtitle and a (pulsing) status dot."""

    def __init__(self, master, title: str, subtitle: str = ""):
        super().__init__(master, pad=14)
        b = self.body
        top = tk.Frame(b, bg=CARD)
        top.pack(fill="x")
        self.dot = tk.Canvas(top, width=12, height=12, bg=CARD, highlightthickness=0, bd=0)
        self.dot.pack(side="left", padx=(0, 8))
        self._oval = self.dot.create_oval(1, 1, 11, 11, fill=MUTED, outline="")
        tk.Label(top, text=title.lower(), bg=CARD, fg=MUTED, font=(UI, 9)).pack(side="left")
        self.value = tk.Label(b, text="-", bg=CARD, fg=FG, font=(UI, 16, "bold"), anchor="w")
        self.value.pack(fill="x", pady=(6, 0))
        self.sub = tk.Label(b, text=subtitle, bg=CARD, fg=MUTED, font=(UI, 9), anchor="w")
        self.sub.pack(fill="x")
        self.colour, self.pulse, self._phase = MUTED, False, False

    def set(self, text: str, colour: str, pulse: bool = False, sub: "str | None" = None) -> None:
        self.value.config(text=text, fg=colour if colour != MUTED else FG)
        self.colour, self.pulse = colour, pulse
        self.dot.itemconfig(self._oval, fill=colour)
        if sub is not None:
            self.sub.config(text=sub)

    def tick(self) -> None:
        if self.pulse:
            self._phase = not self._phase
            self.dot.itemconfig(self._oval, fill=blend(self.colour, CARD, 0.65) if self._phase else self.colour)


class Chip(tk.Label):
    """Small selectable filter chip."""

    def __init__(self, master, text, command):
        super().__init__(master, text=text, font=(UI, 9, "bold"), padx=12, pady=4, cursor="hand2")
        self.command, self.active = command, False
        self.bind("<Button-1>", lambda e: self.command())
        self.bind("<Enter>", lambda e: self._paint(over=True))
        self.bind("<Leave>", lambda e: self._paint())
        self._paint()

    def _paint(self, over: bool = False) -> None:
        if self.active:
            self.config(bg=ACCENT, fg="#ffffff")
        else:
            self.config(bg=GHOST_HOVER if over else GHOST, fg=MUTED if not over else FG)

    def set_active(self, value: bool) -> None:
        self.active = value
        self._paint()


# -------------------------------------------------------------------- app
class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        global UI, MONO
        installed = {f.lower(): f for f in tkfont.families(self)}
        UI = MONO = next((installed[n.lower()] for n in FONT_CHOICES if n.lower() in installed),
                         "TkFixedFont")
        self.title("ExecutorOnDiscord - Control Panel")
        self.geometry("980x740")
        self.minsize(860, 640)
        self.configure(bg=BG)

        self.proc: "subprocess.Popen | None" = None
        self.lines: "queue.Queue[tuple]" = queue.Queue()
        self.clients = 0
        self.bot_state = "stopped"  # stopped | starting | online
        self.stopping = False
        self.started_at: "float | None" = None
        self.entries: list = []
        self.filter_name = "All"
        self._toast_job = None
        self.ws_port = read_bot_constant("WS_PORT", r"(\d+)", "8765")

        self._build()
        self.token_var.set(load_saved_token())

        self.after(100, self._drain_queue)
        self.after(500, self._tick)
        self._poll_roblox()
        self._refresh_status()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        if not BOT_FILE.is_file():
            self._log("ERROR", f"bot.py not found next to gui.py ({APP_DIR})")
        else:
            self._log("INFO", "Ready. Paste your token and press Start bot.")

    # ------------------------------------------------------------- layout
    def _build(self) -> None:
        root = tk.Frame(self, bg=BG)
        root.pack(fill="both", expand=True, padx=20, pady=18)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(3, weight=1)

        self.banner = Banner(root)
        self.banner.grid(row=0, column=0, sticky="ew")

        # status cards
        row = tk.Frame(root, bg=BG)
        row.grid(row=1, column=0, sticky="ew", pady=(14, 0))
        for i in range(3):
            row.columnconfigure(i, weight=1, uniform="cards")
        self.card_bot = StatusCard(row, "Discord bot", "bot.py")
        self.card_roblox = StatusCard(row, "Roblox", "RobloxPlayerBeta.exe")
        self.card_bridge = StatusCard(row, "Bridge clients", f"ws://localhost:{self.ws_port}")
        self.card_bot.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
        self.card_roblox.grid(row=0, column=1, sticky="nsew", padx=7)
        self.card_bridge.grid(row=0, column=2, sticky="nsew", padx=(7, 0))

        # controls
        ctrl = Card(root)
        ctrl.grid(row=2, column=0, sticky="ew", pady=(14, 0))
        c = ctrl.body
        c.columnconfigure(0, weight=1)
        head = tk.Frame(c, bg=CARD)
        head.grid(row=0, column=0, columnspan=3, sticky="ew")
        tk.Label(head, text="Bot token", bg=CARD, fg=FG, font=(UI, 11, "bold")).pack(side="left")
        tk.Label(head, text="   kept only in token.txt (git-ignored)", bg=CARD, fg=MUTED,
                 font=(UI, 9)).pack(side="left")

        self.token_var = tk.StringVar()
        self.entry_wrap = tk.Frame(c, bg=BORDER)
        self.entry_wrap.grid(row=1, column=0, sticky="ew", pady=(10, 0), padx=(0, 10))
        inner = tk.Frame(self.entry_wrap, bg=CARD_2)
        inner.pack(fill="x", padx=1, pady=1)
        self.token_entry = tk.Entry(inner, textvariable=self.token_var, show="•", bg=CARD_2, fg=FG,
                                    insertbackground=FG, relief="flat", bd=0, font=(MONO, 11),
                                    highlightthickness=0)
        self.token_entry.pack(fill="x", padx=12, ipady=9)
        self.token_entry.bind("<FocusIn>", lambda e: self.entry_wrap.config(bg=ACCENT))
        self.token_entry.bind("<FocusOut>", lambda e: self.entry_wrap.config(bg=BORDER))

        self.eye = RoundedButton(c, "👁  Show", self._toggle_show, bg=GHOST, hover=GHOST_HOVER,
                                 parent_bg=CARD, height=40, min_width=92)
        self.eye.grid(row=1, column=1, pady=(10, 0), padx=(0, 8))
        RoundedButton(c, "💾  Save", self.save_token, bg=GHOST, hover=GHOST_HOVER,
                      parent_bg=CARD, height=40, min_width=92).grid(row=1, column=2, pady=(10, 0))

        actions = tk.Frame(c, bg=CARD)
        actions.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(14, 0))
        self.btn_start = RoundedButton(actions, "▶  Start bot", self.start_bot, bg=GREEN,
                                       hover=GREEN_HOVER, fg="#08130d", height=42, min_width=130)
        self.btn_stop = RoundedButton(actions, "■  Stop", self.stop_bot, bg=RED, hover=RED_HOVER,
                                      height=42, min_width=96)
        self.btn_restart = RoundedButton(actions, "↻  Restart", self.restart_bot, bg=ACCENT,
                                         hover=ACCENT_HOVER, height=42, min_width=110)
        self.btn_start.pack(side="left")
        self.btn_stop.pack(side="left", padx=10)
        self.btn_restart.pack(side="left")
        for text, cmd in (("📁  Folder", lambda: open_folder(APP_DIR)),
                          ("🌐  Dev Portal", lambda: webbrowser.open(DEV_PORTAL)),
                          ("📋  Loadstring", self.copy_loadstring)):
            RoundedButton(actions, text, cmd, bg=GHOST, hover=GHOST_HOVER, height=42).pack(
                side="right", padx=(10, 0))

        # console
        cons = Card(root, pad=14)
        cons.grid(row=3, column=0, sticky="nsew", pady=(14, 0))
        b = cons.body
        b.columnconfigure(0, weight=1)
        b.rowconfigure(1, weight=1)
        bar = tk.Frame(b, bg=CARD)
        bar.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        tk.Label(bar, text="Console", bg=CARD, fg=FG, font=(UI, 11, "bold")).pack(side="left")
        chips = tk.Frame(bar, bg=CARD)
        chips.pack(side="left", padx=18)
        self.chips = {}
        for name in FILTERS:
            chip = Chip(chips, name, lambda n=name: self.set_filter(n))
            chip.pack(side="left", padx=(0, 6))
            self.chips[name] = chip
        self.chips["All"].set_active(True)
        RoundedButton(bar, "Clear", self.clear_log, bg=GHOST, hover=GHOST_HOVER, height=30,
                      padx=14, radius=8, font=tkfont.Font(family=UI, size=9, weight="bold")).pack(side="right")
        RoundedButton(bar, "Save log", self.save_log, bg=GHOST, hover=GHOST_HOVER, height=30,
                      padx=14, radius=8, font=tkfont.Font(family=UI, size=9, weight="bold")).pack(
            side="right", padx=8)

        self.text = tk.Text(b, bg="#0b0c10", fg=FG, insertbackground=FG, relief="flat", bd=0,
                            font=(MONO, 10), wrap="word", state="disabled", padx=12, pady=10,
                            highlightthickness=0, spacing1=2, spacing3=2)
        sb = tk.Scrollbar(b, command=self.text.yview, bg=CARD, troughcolor=CARD, bd=0,
                          relief="flat", highlightthickness=0, width=10)
        self.text.configure(yscrollcommand=sb.set)
        self.text.grid(row=1, column=0, sticky="nsew")
        sb.grid(row=1, column=1, sticky="ns", padx=(6, 0))
        self.text.tag_configure("time", foreground=MUTED)
        self.text.tag_configure("plain", foreground=FG)
        for label, colour in LABEL_COLOURS.items():
            self.text.tag_configure(f"b_{label}", background=colour, foreground="#0b0c10",
                                    font=(MONO, 9, "bold"))
            msg_colour = colour if label in ("ERROR", "WARN", "DISC") else FG
            self.text.tag_configure(f"m_{label}", foreground=msg_colour)

        # footer
        foot = tk.Frame(root, bg=BG)
        foot.grid(row=4, column=0, sticky="ew", pady=(10, 0))
        tk.Label(foot, text="Treat your token like a password.", bg=BG, fg=MUTED,
                 font=(UI, 9)).pack(side="left")
        self.top_var = tk.BooleanVar(value=False)
        tk.Checkbutton(foot, text="Always on top", variable=self.top_var, command=self._toggle_top,
                       bg=BG, fg=MUTED, selectcolor=CARD_2, activebackground=BG,
                       activeforeground=FG, font=(UI, 9), bd=0, highlightthickness=0).pack(side="right")

        # toast
        self.toast = tk.Label(self, text="", bg=ACCENT, fg="#ffffff", font=(UI, 10, "bold"),
                              padx=16, pady=9)

    # ------------------------------------------------------------ helpers
    def _toggle_show(self) -> None:
        hidden = self.token_entry.cget("show") != ""
        self.token_entry.config(show="" if hidden else "•")
        self.eye.text = "🙈  Hide" if hidden else "👁  Show"
        self.eye._draw()

    def _toggle_top(self) -> None:
        self.attributes("-topmost", bool(self.top_var.get()))

    def show_toast(self, message: str, colour: str = ACCENT) -> None:
        if self._toast_job:
            self.after_cancel(self._toast_job)
        self.toast.config(text=message, bg=colour)
        self.toast.place(relx=1.0, rely=1.0, anchor="se", x=-28, y=-48)
        self.toast.lift()
        self._toast_job = self.after(2200, self.toast.place_forget)

    def set_filter(self, name: str) -> None:
        self.filter_name = name
        for key, chip in self.chips.items():
            chip.set_active(key == name)
        self.text.config(state="normal")
        self.text.delete("1.0", "end")
        self.text.config(state="disabled")
        for entry in self.entries:
            self._render(entry)

    def _visible(self, label: str) -> bool:
        allowed = FILTERS[self.filter_name]
        return allowed is None or label in allowed

    def _render(self, entry) -> None:
        stamp, label, message = entry
        if not self._visible(label):
            return
        self.text.config(state="normal")
        self.text.insert("end", stamp + "  ", "time")
        if label in LABEL_COLOURS:
            self.text.insert("end", f" {label:^6} ", f"b_{label}")
            self.text.insert("end", "  " + message + "\n", f"m_{label}")
        else:
            self.text.insert("end", message + "\n", "plain")
        if int(self.text.index("end-1c").split(".")[0]) > 2000:
            self.text.delete("1.0", "300.0")
        self.text.see("end")
        self.text.config(state="disabled")

    def _log(self, label: str, message: str, stamp: "str | None" = None) -> None:
        stamp = stamp or datetime.datetime.now().strftime("%H:%M:%S")
        entry = (stamp, label, message)
        self.entries.append(entry)
        if len(self.entries) > 3000:
            del self.entries[:500]
        self._render(entry)

    def clear_log(self) -> None:
        self.entries.clear()
        self.text.config(state="normal")
        self.text.delete("1.0", "end")
        self.text.config(state="disabled")

    def save_log(self) -> None:
        path = filedialog.asksaveasfilename(
            defaultextension=".txt", initialfile="bot-log.txt",
            filetypes=[("Text file", "*.txt"), ("All files", "*.*")])
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as fh:
                for stamp, label, message in self.entries:
                    fh.write(f"{stamp} [{label or '-'}] {message}\n")
            self.show_toast("Log saved", GREEN)
        except OSError as exc:
            messagebox.showerror("Save log", str(exc))

    def copy_loadstring(self) -> None:
        snippet = f'loadstring(game:HttpGet("{read_loadstring_url()}"))()'
        self.clipboard_clear()
        self.clipboard_append(snippet)
        self.show_toast("Loadstring copied", ACCENT)
        self._log("INFO", "Loadstring copied. Run it in your executor.")

    def save_token(self) -> bool:
        token = self.token_var.get().strip().strip("\"'")
        if token.lower().startswith("bot "):
            token = token[4:].strip()
        if not token:
            messagebox.showwarning("Token", "Paste your bot token first.")
            return False
        if not looks_like_token(token) and not messagebox.askyesno(
                "Token", "This does not look like a Discord bot token.\nSave it anyway?"):
            return False
        try:
            TOKEN_FILE.write_text(token + "\n", encoding="utf-8")
            gitignore = APP_DIR / ".gitignore"
            existing = gitignore.read_text(encoding="utf-8") if gitignore.is_file() else ""
            if "token.txt" not in existing.splitlines():
                with gitignore.open("a", encoding="utf-8") as fh:
                    if existing and not existing.endswith("\n"):
                        fh.write("\n")
                    fh.write("token.txt\n")
        except OSError as exc:
            messagebox.showerror("Token", f"Could not save token:\n{exc}")
            return False
        self.token_var.set(token)
        self.show_toast("Token saved", GREEN)
        self._log("OK", "Token saved to token.txt (added to .gitignore).")
        return True

    # ------------------------------------------------------- bot control
    @property
    def running(self) -> bool:
        return self.proc is not None and self.proc.poll() is None

    def start_bot(self) -> None:
        if self.running:
            return
        if not BOT_FILE.is_file():
            messagebox.showerror("bot.py", f"bot.py was not found in:\n{APP_DIR}")
            return
        token = self.token_var.get().strip().strip("\"'")
        if token.lower().startswith("bot "):
            token = token[4:].strip()
        if not token:
            self.show_toast("Enter your bot token first", YELLOW)
            self.token_entry.focus_set()
            return
        if not looks_like_token(token) and not messagebox.askyesno(
                "Token", "That does not look like a bot token.\nStart anyway?"):
            return

        env = os.environ.copy()
        env["DISCORD_BOT_TOKEN"] = token
        env["PYTHONUNBUFFERED"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        try:
            self.proc = subprocess.Popen(
                [python_executable(), "-u", str(BOT_FILE)],
                cwd=str(APP_DIR), env=env, stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace", bufsize=1,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except OSError as exc:
            messagebox.showerror("Start", f"Could not start the bot:\n{exc}")
            return

        self.stopping = False
        self.clients = 0
        self.bot_state = "starting"
        self.started_at = time.time()
        self._log("INFO", "Starting bot.py ...")
        threading.Thread(target=self._reader, args=(self.proc,), daemon=True).start()
        self._refresh_status()

    def stop_bot(self) -> None:
        if not self.running:
            return
        self.stopping = True
        self._log("WARN", "Stopping bot ...")
        proc = self.proc

        def killer() -> None:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass

        threading.Thread(target=killer, daemon=True).start()

    def restart_bot(self) -> None:
        if self.running:
            self.stop_bot()
            self._wait_then_start()
        else:
            self.start_bot()

    def _wait_then_start(self) -> None:
        if self.running:
            self.after(200, self._wait_then_start)
        else:
            self.start_bot()

    def _reader(self, proc: "subprocess.Popen") -> None:
        try:
            for raw in proc.stdout:  # type: ignore[union-attr]
                self.lines.put(("line", raw.rstrip("\r\n")))
        except Exception:
            pass
        self.lines.put(("exit", proc.wait()))

    def _drain_queue(self) -> None:
        try:
            while True:
                kind, payload = self.lines.get_nowait()
                if kind == "line":
                    self._handle_line(payload)
                elif kind == "roblox":
                    self.card_roblox.set("Running" if payload else "Not found",
                                         GREEN if payload else MUTED, pulse=bool(payload))
                else:
                    self._handle_exit(payload)
        except queue.Empty:
            pass
        self.after(100, self._drain_queue)

    def _handle_line(self, raw: str) -> None:
        line = ANSI_RE.sub("", raw)
        if not line.strip():
            return
        m = LOG_LINE_RE.match(line)
        if m:
            stamp, label, message = m.groups()
            self._log(label.upper(), message, stamp)
        else:
            message = line
            self._log("", line)

        low = message.lower()
        if "logged in as" in low:
            self.bot_state = "online"
            self.show_toast("Bot is online", GREEN)
        total = TOTAL_RE.search(message)
        if total and "connected" in low:
            self.clients = int(total.group(1))
        if "disallowed intents" in low:
            self._log("WARN", "Tip: Developer Portal → Bot → enable 'Message Content Intent', then Save.")
        if "improper token" in low or "invalid token" in low or "loginfailure" in low:
            self._log("WARN", "Tip: the token is wrong or was reset. Reset it and paste the new one.")
        self._refresh_status()

    def _handle_exit(self, code: int) -> None:
        self.bot_state, self.clients, self.started_at = "stopped", 0, None
        if self.stopping:
            self._log("INFO", "Bot stopped.")
        else:
            self._log("ERROR" if code else "INFO", f"Bot exited with code {code}.")
            if code:
                self.show_toast("Bot stopped with an error", RED)
        self.stopping = False
        self._refresh_status()

    # ------------------------------------------------------------ status
    def _refresh_status(self) -> None:
        if self.bot_state == "online":
            self.card_bot.set("Online", GREEN, pulse=True)
        elif self.bot_state == "starting":
            self.card_bot.set("Starting…", YELLOW, pulse=True, sub="logging in")
        else:
            self.card_bot.set("Stopped", RED, sub="bot.py")

        if self.clients > 0:
            self.card_bridge.set(f"{self.clients} connected", GREEN, pulse=True)
        else:
            self.card_bridge.set("None", YELLOW if self.bot_state == "online" else MUTED)

        running = self.running
        self.btn_start.set_enabled(not running)
        self.btn_stop.set_enabled(running)
        self.banner.set_live(self.bot_state == "online")

    def _tick(self) -> None:
        for card in (self.card_bot, self.card_roblox, self.card_bridge):
            card.tick()
        if self.bot_state == "online" and self.started_at:
            self.card_bot.sub.config(text=f"uptime {fmt_duration(time.time() - self.started_at)}")
        self.after(600, self._tick)

    def _poll_roblox(self) -> None:
        if psutil is None:
            self.card_roblox.set("Unknown", MUTED, sub="pip install psutil")
            return

        def worker() -> None:
            try:
                found = any((p.info["name"] or "").lower() == "robloxplayerbeta.exe"
                            for p in psutil.process_iter(["name"]))
            except Exception:
                found = False
            self.lines.put(("roblox", found))  # handled on the Tk thread

        threading.Thread(target=worker, daemon=True).start()
        self.after(3000, self._poll_roblox)

    # -------------------------------------------------------------- exit
    def _on_close(self) -> None:
        if self.running:
            if not messagebox.askyesno("Quit", "The bot is still running. Stop it and quit?"):
                return
            try:
                self.proc.terminate()  # type: ignore[union-attr]
            except Exception:
                pass
        self.destroy()


if __name__ == "__main__":
    App().mainloop()
