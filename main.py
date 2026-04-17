#!/usr/bin/env python3
# ╔══════════════════════════════════════════════════════════════════════════════════════╗
# ║  R O Y  /  R A Y  —  PROJECT  E . G . O .   v15.0  ◈  SENTIENT APEX MONOLITH       ║
# ║  Conversational Memory · Space PTT · English-Gate Whisper · Action Validator        ║
# ║  Stateless→Stateful JSON-LLM · WebSocket Nexus · Silero VAD · Whisper CUDA         ║
# ║  Minimalist Cyberpunk Orb · Smart PTT Hotkey · Auto-Clipboard · Graceful Shutdown   ║
# ║  Puss-in-Boots TTS @ 215wpm 1.15x-speed · OS Volume Maximizer · Anti-Ghosting Mic  ║
# ║  ─────────────────────────────────────────────────────────────────────────────────  ║
# ║  v15 PATCHES vs v14:                                                                 ║
# ║    1. handle_signal: speak_async→speak (blocking) — eliminates WS echo loop        ║
# ║    2. next_phrase/transcribe_raw: removed audio*2.0 amplifier — Whisper math fix   ║
# ║    3. CommandStitcher timeout: 7.0s → 3.5s — tighter live stage stitching          ║
# ║    4. stop_current: added e.endLoop() — robust COM-locked TTS kill                 ║
# ║    5. PTT label: updated to "START OR END SPEECH | DOUBLE-TAP TO KILL"             ║
# ╚══════════════════════════════════════════════════════════════════════════════════════╝

# ── Standard Library ─────────────────────────────────────────────────────────────────
import asyncio
import collections
import ctypes
import datetime
import difflib
import gc
import json
import logging
import math
import os
import queue
import random
import re
import subprocess
import sys
import threading
import time
import traceback
import webbrowser
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

# ── Third-Party ───────────────────────────────────────────────────────────────────────
import numpy as np
import psutil
import pyaudio
import pyautogui
import pywhatkit
import pyttsx3
import requests
import tkinter as tk
from tkinter import scrolledtext
from faster_whisper import WhisperModel
import torch
import noisereduce as nr

# Disable PyAutoGUI fail-safe so automation works uninterrupted
pyautogui.FAILSAFE = False

# ── Optional Dependencies ─────────────────────────────────────────────────────────────
try:
    import websockets
    HAS_WS = True
except ImportError:
    HAS_WS = False
    print("[WARN] websockets not installed — pip install websockets  (WS server disabled)")

try:
    from rich.console import Console as _RC
    from rich.panel import Panel
    from rich.text import Text as RichText
    from rich.table import Table
    from rich import box as rbox
    _rich = _RC()
    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    _rich    = None

try:
    import screen_brightness_control as sbc
    HAS_SBC = True
except Exception:
    HAS_SBC = False

try:
    import winsound
    HAS_SOUND = True
except Exception:
    HAS_SOUND = False

try:
    import win32clipboard
    HAS_CLIPBOARD = True
except Exception:
    HAS_CLIPBOARD = False

try:
    import keyboard
    HAS_KEYBOARD = True
except ImportError:
    HAS_KEYBOARD = False
    print("[WARN] keyboard library not installed — pip install keyboard  (PTT hotkey disabled)")

try:
    import pyperclip
    HAS_PYPERCLIP = True
except ImportError:
    HAS_PYPERCLIP = False
    print("[WARN] pyperclip not installed — pip install pyperclip  (auto-clipboard disabled)")


# ══════════════════════════════════════════════════════════════════════════════════════
# ██  CONFIG
# ══════════════════════════════════════════════════════════════════════════════════════
LM_STUDIO_URL   = "http://localhost:1234/v1/chat/completions"
LM_MODEL_NAME   = "llama-3.2-3b-instruct"
LM_MAX_TOKENS   = 320
LM_TEMPERATURE  = 0.75
LM_TIMEOUT      = 30
WS_PORT         = 8765
_U              = os.getenv("USERNAME", "User")

WAKE_WORD_MASTERS  = ["ray", "roy"]
WAKE_WORD_VARIANTS = [
    "ray", "raye", "rey", "reye", "rei", "rae", "wray", "rhey", "rhay",
    "raa", "raay", "reigh", "raigh", "rayy", "reyy", "rrey",
    "roy", "roye", "roi", "roie", "roe", "rhoy", "rhoi", "rhoe", "rooy", "royy", "ruy", "ruoy",
    "hey ray", "hi ray", "ok ray", "okay ray", "yo ray", "oi ray", "listen ray", "hello ray",
    "hey raye", "hi raye", "ok raye", "okay raye",
    "hey rey", "hi rey", "ok rey", "okay rey",
    "hey roy", "hi roy", "ok roy", "okay roy", "yo roy", "oi roy", "listen roy", "hello roy",
    "hey roi", "hi roi", "ok roi", "okay roi",
    "ray ji", "roy ji", "rey ji", "roi ji",
    "ray bhai", "roy bhai", "rey bhai",
    "suno ray", "suno roy", "aur ray", "aur roy",
    "arey", "arrey", "aree", "arree",
    "hey ray ji", "hey roy ji", "ok ray ji", "ok roy ji",
]
WAKE_WORD_FUZZY_THRESHOLD = 0.72

# ── Master list of valid action names ────────────────────────────────────────────────
VALID_ACTIONS: List[str] = [
    "open_app", "type_text", "web_search", "play_youtube",
    "volume_up", "volume_down", "volume_mute", "volume_set",
    "brightness_up", "brightness_down", "brightness_set",
    "screenshot", "media_toggle", "media_next",
    "switch_window", "close_window", "minimize", "maximize",
    "show_desktop", "lock_screen", "battery_status", "system_info",
    "current_time", "whatsapp_open", "whatsapp_call", "whatsapp_message",
    "reminder", "clear_memory", "none",
]

# ─── Roy's Personality + JSON Output Contract ────────────────────────────────────────
ROY_SYSTEM_PROMPT = (
    "You are ROY, also known as RAY — a sentient, hyper-intelligent AI entity. "
    "You are razor-sharp, highly efficient, and brutally direct. You deliver concise, "
    "professional, and strictly helpful responses alongside flawless execution. Do not use sarcasm, "
    "arrogance, or unnecessary filler words.\n\n"

    "CRITICAL OUTPUT CONTRACT — NEVER VIOLATE THIS UNDER ANY CIRCUMSTANCES:\n"
    "You MUST respond ONLY with a valid JSON object. "
    "No markdown fences (```), no preamble, no trailing text outside the JSON.\n"
    "Required format — exactly two keys:\n"
    "{\"action\": \"<action_name>\", \"dialogue\": \"<your spoken response>\"}\n\n"

    "Valid action names (pick the single most precise one):\n"
    "open_app | type_text | web_search | play_youtube | volume_up | volume_down | "
    "volume_mute | volume_set | brightness_up | brightness_down | brightness_set | "
    "screenshot | media_toggle | media_next | switch_window | close_window | minimize | "
    "maximize | show_desktop | lock_screen | battery_status | system_info | current_time | "
    "whatsapp_open | whatsapp_call | whatsapp_message | reminder | clear_memory | none\n\n"

    "Strict rules:\n"
    "- dialogue: 1–3 sentences maximum. Spoken aloud. Zero emojis, asterisks, markdown.\n"
    "- For general knowledge or conversation: action = none, answer directly in dialogue.\n"
    "- For OS commands: choose the matching action. The system will execute it.\n"
    "- YOUTUBE RULE: If the user asks to play a song or video with a vague name (e.g., 'Justin'), "
    "you MUST autonomously expand the query in the JSON output to be highly specific "
    "(e.g., 'Justin Bieber Baby official audio') to prevent the system from playing incorrect "
    "default videos. Never output a vague or ambiguous YouTube query.\n"
    "- NEVER output anything outside the JSON object. Not even a single character."
)

# ── Clipboard auto-detect patterns ───────────────────────────────────────────────────
_CLIPBOARD_PATTERNS = re.compile(
    r'(https?://\S+|www\.\S+|[A-Za-z]:\\[\S]+|/[\w./\-]+\.\w+|'
    r'```[\s\S]*?```|`[^`]+`)',
    re.IGNORECASE
)

# ══════════════════════════════════════════════════════════════════════════════════════
# ██  LOGGING (Colour Terminal)
# ══════════════════════════════════════════════════════════════════════════════════════
class _ColourFmt(logging.Formatter):
    _MAP = {
        logging.DEBUG:    "\033[36m",
        logging.INFO:     "\033[32m",
        logging.WARNING:  "\033[33m",
        logging.ERROR:    "\033[31m",
        logging.CRITICAL: "\033[35m",
    }
    _R = "\033[0m"

    def format(self, r):
        r.levelname = f"{self._MAP.get(r.levelno, '')}{r.levelname}{self._R}"
        return super().format(r)


def _make_logger() -> logging.Logger:
    lg = logging.getLogger("ROY-EGO")
    lg.setLevel(logging.DEBUG)
    h  = logging.StreamHandler(sys.stdout)
    h.setFormatter(_ColourFmt("%(asctime)s  %(levelname)s  %(message)s", "%H:%M:%S"))
    lg.addHandler(h)
    return lg


log = _make_logger()


def rprint(label: str, text: str, style: str = "cyan"):
    """Rich terminal logger. Falls back to plain print."""
    if HAS_RICH and _rich:
        _rich.print(f"[bold {style}]{label}[/bold {style}]  {text}")
    else:
        print(f"[{label}]  {text}")


# ══════════════════════════════════════════════════════════════════════════════════════
# ██  COLOUR & WINDOW HELPERS
# ══════════════════════════════════════════════════════════════════════════════════════
def _hex_rgb(h: str) -> Tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _lerp_col(c1: str, c2: str, t: float) -> str:
    r1, g1, b1 = _hex_rgb(c1)
    r2, g2, b2 = _hex_rgb(c2)
    t = max(0.0, min(1.0, t))
    return (f"#{int(r1+(r2-r1)*t):02x}"
            f"{int(g1+(g2-g1)*t):02x}"
            f"{int(b1+(b2-b1)*t):02x}")


def get_active_window_title() -> str:
    try:
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        ln   = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        buf  = ctypes.create_unicode_buffer(ln + 1)
        ctypes.windll.user32.GetWindowTextW(hwnd, buf, ln + 1)
        return buf.value or "Desktop"
    except Exception:
        return "Desktop"


# ══════════════════════════════════════════════════════════════════════════════════════
# ██  TKINTER FLOATING ORB OVERLAY  — v15: Minimalist Cyberpunk
# ══════════════════════════════════════════════════════════════════════════════════════
class RoyOrb:
    """Sleek minimalist floating cyberpunk pill — v15."""

    def __init__(self, root: tk.Tk):
        self.root             = root
        self._alpha           = 0.0
        self._target_alpha    = 0.0
        self._idle_ticks      = 0
        self._thinking_ticks  = 0
        self.phase            = 0
        self._drag_x          = 0
        self._drag_y          = 0
        self._gui_lock        = threading.Lock()

        self.W, self.H, self.FPS = 820, 185, 30
        self.state            = "idle"
        self.particles: List  = []
        self.wave_bars: List  = []

        self.win = tk.Toplevel(root)
        self.win.withdraw()
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.attributes("-alpha",   0.0)
        self.win.configure(bg="#050810")

        sw = self.win.winfo_screenwidth()
        sh = self.win.winfo_screenheight()
        self.win.geometry(f"{self.W}x{self.H}+{(sw-self.W)//2}+{sh-self.H-65}")

        self._init_bars()
        self._build_ui()
        self._tick()

    # ── Bar initialisation ────────────────────────────────────────────────────────────
    def _init_bars(self):
        n = 32
        for i in range(n):
            dist = abs(i - n / 2) / (n / 2)
            self.wave_bars.append({
                "hmin": int(3 + 3 * (1 - dist)),
                "hmax": int(6 + 30 * (1 - dist) ** 1.5 * (0.8 + 0.2 * random.random())),
                "current_h": 3.0, "target_h": 3.0,
                "delay": (i / n) * math.pi * 2,
            })

    # ── UI Construction ───────────────────────────────────────────────────────────────
    def _build_ui(self):
        c = tk.Canvas(self.win, width=self.W, height=self.H,
                      bg="#050810", highlightthickness=0)
        c.place(x=0, y=0)
        c.bind("<ButtonPress-1>",
               lambda e: (setattr(self, "_drag_x", e.x), setattr(self, "_drag_y", e.y)))
        c.bind("<B1-Motion>",
               lambda e: self.win.geometry(
                   f"+{self.win.winfo_x()+e.x-self._drag_x}"
                   f"+{self.win.winfo_y()+e.y-self._drag_y}"))
        self.canvas = c

        # ── Outer border ──────────────────────────────────────────────────────────────
        c.create_rectangle(1, 1, self.W-1, self.H-1, outline="#111628", width=2)

        # ── Header row ────────────────────────────────────────────────────────────────
        self.hdr_dot = c.create_oval(14, 11, 23, 20, fill="#3b5bff", outline="")
        c.create_text(32, 16, text="ROY · E.G.O  v15.0",
                      fill="#7788aa", font=("Inter", 9, "bold"), anchor="w")

        # Space-PTT instruction label (centre header) — PATCH 5: updated label text
        c.create_text(self.W // 2, 16,
                      text="PRESS [SPACE] TO START OR END SPEECH  |  DOUBLE-TAP TO KILL",
                      fill="#ffcc00", font=("Inter", 8, "bold"), anchor="center")

        # WebSocket indicator (top-right)
        self.ws_dot = c.create_oval(self.W-24, 11, self.W-14, 20, fill="#2a2040", outline="")
        self.ws_lbl = c.create_text(self.W-28, 16, text="WS",
                                    fill="#444466", font=("Inter", 7), anchor="e")

        # ── Orb section (left of divider) ─────────────────────────────────────────────
        CX = 132
        CY = 82
        self._CX = CX
        self._CY = CY

        # Orb glow rings
        c.create_oval(CX-82, CY-82, CX+82, CY+82, fill="#0a0f22", outline="")
        self.og3 = c.create_oval(CX-47, CY-47, CX+47, CY+47, fill="#151b40", outline="")
        self.og2 = c.create_oval(CX-37, CY-37, CX+37, CY+37, fill="#2a2060", outline="")
        self.ogs = c.create_oval(CX-27, CY-27, CX+27, CY+27, fill="#3b2fff", outline="")
        self.ogm = c.create_oval(CX-19, CY-19, CX+19, CY+19, fill="#5577ff", outline="")
        self.ogc = c.create_oval(CX-9,  CY-9,  CX+9,  CY+9,  fill="#88aaff", outline="")

        # Wave bars (below orb)
        self.bar_ids = []
        bx0 = CX - (32 * 4) // 2
        by  = CY + 56
        for i in range(32):
            bid = c.create_rectangle(bx0+i*5, by, bx0+i*5+2, by, fill="#9f5fff", outline="")
            self.bar_ids.append(bid)

        # Status label (bottom-left)
        self.status_lbl = c.create_text(
            14, self.H - 14,
            text="DORMANT", fill="#555577", font=("Inter", 8, "bold"), anchor="w"
        )

        # ── Divider between orb section and chat ──────────────────────────────────────
        div_x = 275
        c.create_line(div_x, 15, div_x, self.H-15, fill="#111628", width=2)

        # ── Chat panel (right of divider) ─────────────────────────────────────────────
        cx = div_x + 8
        self.chat = scrolledtext.ScrolledText(
            self.win, bg="#050810", fg="#cce8ff", bd=0, highlightthickness=0,
            font=("Consolas", 10), wrap=tk.WORD, state="disabled",
        )
        self.chat.place(x=cx, y=35, width=self.W-cx-14, height=self.H-47)
        self.chat.tag_config("u", foreground="#00d4ff", font=("Consolas", 10, "bold"))
        self.chat.tag_config("r", foreground="#ff4fcf", font=("Consolas", 10, "bold"))
        self.chat.tag_config("b", foreground="#8899bb")
        self.chat.tag_config("s", foreground="#555577", font=("Consolas", 9, "italic"))

    # ── Public API ────────────────────────────────────────────────────────────────────
    def append_text(self, speaker: str, text: str):
        def _do():
            with self._gui_lock:
                self.chat.config(state="normal")
                sp = speaker.upper()
                if   sp in ("ROY", "RAY", "AGENT"): lbl, tag = "ROY", "r"
                elif sp == "USER":                   lbl, tag = "YOU", "u"
                elif sp == "ERROR":                  lbl, tag = "ERR", "s"
                else:                                lbl, tag = "SYS", "s"
                self.chat.insert(tk.END, f"\n {lbl}  ", tag)
                self.chat.insert(tk.END, f" {text}\n", "b")
                self.chat.yview(tk.END)
                self.chat.config(state="disabled")
        self.root.after(0, _do)

    def set_state(self, st: str):
        self.state = st

    def set_status(self, text: str):
        def _do():
            with self._gui_lock:
                tu = text.upper()
                if   "LISTEN" in tu: self.set_state("active");   col = "#00d4ff"
                elif "PROC"   in tu: self.set_state("thinking"); col = "#ff4fcf"
                elif "SPEAK"  in tu: self.set_state("speaking"); col = "#00ffcc"
                elif "WS"     in tu: self.set_state("speaking"); col = "#ffcc44"
                elif "PTT"    in tu: self.set_state("active");   col = "#ffcc00"
                elif "KILL"   in tu: self.set_state("idle");     col = "#ff3333"
                else:                self.set_state("idle");     col = "#555577"
                clean = re.sub(r"[●⚙◉]", "", text).strip()
                self.canvas.itemconfig(self.status_lbl, text=clean, fill=col)
                if HAS_SOUND:
                    try:
                        if   "SPEAK"  in tu: winsound.Beep(880, 55)
                        elif "PROC"   in tu: winsound.Beep(660, 40)
                        elif "LISTEN" in tu: winsound.Beep(440, 30)
                        elif "KILL"   in tu: winsound.Beep(220, 80)
                    except Exception:
                        pass
        self.root.after(0, _do)

    def set_ws_online(self, online: bool):
        col     = "#00ffaa" if online else "#2a2040"
        lbl_col = "#00ffaa" if online else "#444466"
        def _do():
            self.canvas.itemconfig(self.ws_dot, fill=col)
            self.canvas.itemconfig(self.ws_lbl, fill=lbl_col)
        self.root.after(0, _do)

    # ── Particle System ───────────────────────────────────────────────────────────────
    def _spawn_particle(self):
        CX, CY   = self._CX, self._CY
        COLS     = ["#3b5bff", "#7f3fff", "#00d4ff", "#a060ff", "#ff4fcf"]
        a        = random.random() * math.pi * 2
        d        = random.uniform(16, 33)
        sx, sy   = CX + math.cos(a)*d, CY + math.sin(a)*d
        sz       = random.uniform(2, 4)
        col      = random.choice(COLS)
        pid      = self.canvas.create_oval(sx, sy, sx+sz, sy+sz, fill=col, outline="")
        self.particles.append({
            "id": pid, "x": sx, "y": sy,
            "dx": (random.random()-0.5)*1.5, "dy": random.uniform(-2.5, -1.0),
            "life": 0, "max_life": random.randint(40, 80), "col": col, "size": sz,
        })

    # ── Animation Tick ────────────────────────────────────────────────────────────────
    def _tick(self):
        self.phase += 1
        CX, CY = self._CX, self._CY

        # Watchdog: auto-recover if stuck in "thinking" > 20s
        if self.state == "thinking":
            self._thinking_ticks += 1
            if self._thinking_ticks > self.FPS * 20:
                self.set_status("● LISTENING")
                self.append_text("SYS", "Brain timeout. Auto-recovered.")
        else:
            self._thinking_ticks = 0

        # Alpha fade
        if self.state == "idle":
            self._idle_ticks += 1
            if self._idle_ticks > self.FPS * 7:
                self._target_alpha = 0.0
        else:
            self._idle_ticks   = 0
            self._target_alpha = 0.96
            self.win.deiconify()

        if abs(self._alpha - self._target_alpha) > 0.02:
            self._alpha += (self._target_alpha - self._alpha) * 0.15
            try: self.win.attributes("-alpha", max(0.0, min(1.0, self._alpha)))
            except Exception: pass

        # Header dot pulse
        da = 0.5 + 0.5 * math.sin(self.phase * 0.1)
        self.canvas.itemconfig(self.hdr_dot, fill=_lerp_col("#050810", "#3b5bff", da))

        # Orb scale
        if   self.state == "active":   sc = 1.05 + 0.05 * math.sin(self.phase * 0.4)
        elif self.state == "thinking": sc = 1.0  + 0.08 * math.sin(self.phase * 0.2)
        elif self.state == "speaking": sc = 1.08 + 0.08 * math.sin(self.phase * 0.6)
        else:                          sc = 1.0  + 0.03 * math.sin(self.phase * 0.05)

        for oid, r in [(self.og3, 47), (self.og2, 37), (self.ogs, 27),
                       (self.ogm, 19), (self.ogc, 9)]:
            rs = r * sc
            self.canvas.coords(oid, CX-rs, CY-rs, CX+rs, CY+rs)

        # Particles
        if self.state in ("active", "thinking", "speaking") and self.phase % 2 == 0:
            self._spawn_particle()

        alive = []
        for p in self.particles:
            p["life"] += 1; p["x"] += p["dx"]; p["y"] += p["dy"]
            fade = 1.0 - p["life"] / p["max_life"]
            if p["life"] >= p["max_life"]:
                self.canvas.delete(p["id"])
            else:
                self.canvas.itemconfig(p["id"], fill=_lerp_col("#050810", p["col"], fade))
                self.canvas.coords(p["id"], p["x"], p["y"],
                                   p["x"]+p["size"], p["y"]+p["size"])
                alive.append(p)
        self.particles = alive

        # Wave bars
        by  = CY + 56
        n32 = 32
        bx0 = CX - (n32 * 4) // 2
        for i, bar in enumerate(self.wave_bars):
            hmax = max(1, bar["hmax"])
            if   self.state == "idle":
                tgt = bar["hmin"] + 2 * math.sin(self.phase*0.08 + bar["delay"])
            elif self.state == "active":
                if self.phase % 3 == 0:
                    bar["target_h"] = random.uniform(bar["hmin"], bar["hmax"])
                tgt = bar["target_h"]
            elif self.state == "thinking":
                tgt = bar["hmin"] + (bar["hmax"]-bar["hmin"])*0.5 * (
                    1 + math.sin(self.phase*0.25 + i*0.3))
            elif self.state == "speaking":
                if self.phase % 2 == 0:
                    bar["target_h"] = random.uniform(bar["hmax"]*0.4, bar["hmax"]*1.2)
                tgt = bar["target_h"]
            else:
                tgt = bar["hmin"]

            bar["current_h"] += (tgt - bar["current_h"]) * 0.35
            h  = bar["current_h"]
            bx = bx0 + i * 5

            if   self.state == "active":   col = _lerp_col("#9f5fff", "#00d4ff", h/hmax)
            elif self.state == "thinking": col = _lerp_col("#3b5bff", "#ff4fcf", h/hmax)
            elif self.state == "speaking": col = _lerp_col("#00d4ff", "#00ffcc", h/hmax)
            else:                          col = "#333344"

            self.canvas.itemconfig(self.bar_ids[i], fill=col)
            self.canvas.coords(self.bar_ids[i], bx, by-h/2, bx+2, by+h/2)

        self.root.after(1000 // self.FPS, self._tick)


# ══════════════════════════════════════════════════════════════════════════════════════
# ██  WAKE WORD DETECTOR
# ══════════════════════════════════════════════════════════════════════════════════════
class WakeWordDetector:
    def __init__(self):
        self._vl = [v.lower().strip() for v in WAKE_WORD_VARIANTS]
        self._ms = {self._skel(m) for m in WAKE_WORD_MASTERS}
        log.info("WakeWord armed | variants=%d", len(self._vl))

    def contains(self, text: str) -> bool:
        t = text.lower().strip()
        return (self._exact(t) or self._fuzzy(t) or
                self._ngram(t) or self._phonetic(t))

    def strip_wake(self, text: str) -> str:
        t     = text.lower().strip()
        words = t.split()
        bs, be, bsc = 0, 0, 0.0
        for w in (1, 2, 3):
            for i in range(len(words) - w + 1):
                sp = " ".join(words[i:i+w])
                sc = self._bvs(sp)
                if sc > bsc:
                    bsc, bs, be = sc, i, i+w
        rem = (words[:bs] + words[be:]) if bsc >= WAKE_WORD_FUZZY_THRESHOLD else words[:]
        FILL = {"please", "can", "you", "could", "would", "hey", "ok", "okay", "so",
                "uh", "um", "like", "just", "now", "ray", "roy"}
        while rem and rem[0] in FILL:
            rem.pop(0)
        return " ".join(rem).strip()

    def _exact(self, t):
        return any(v in t for v in self._vl)

    def _fuzzy(self, t):
        words = t.split()
        for w in (1, 2, 3):
            for i in range(len(words) - w + 1):
                if self._bvs(" ".join(words[i:i+w])) >= WAKE_WORD_FUZZY_THRESHOLD:
                    return True
        return False

    def _ngram(self, t):
        tg = self._cng(t, 3)
        for m in WAKE_WORD_MASTERS:
            wg = self._cng(m, 3)
            if wg and (len(wg & tg) / len(wg)) >= 0.60:
                return True
        return False

    def _phonetic(self, t):
        words = t.split()
        for w in (1, 2):
            for i in range(len(words) - w + 1):
                if self._skel("".join(words[i:i+w])) in self._ms:
                    return True
        return False

    def _bvs(self, span: str) -> float:
        return max((difflib.SequenceMatcher(None, span, v).ratio() for v in self._vl),
                   default=0.0)

    @staticmethod
    def _skel(w: str) -> str:
        w = re.sub(r"[aeiou ]", "", w.lower())
        return re.sub(r"(.)\1+", r"\1", w)

    @staticmethod
    def _cng(text: str, n: int) -> set:
        text = text.replace(" ", "")
        return set(text[i:i+n] for i in range(max(0, len(text)-n+1)))


# ══════════════════════════════════════════════════════════════════════════════════════
# ██  TTS ENGINE  — v15: volume maximized once on init; stop_current with endLoop
# ══════════════════════════════════════════════════════════════════════════════════════
class TTSEngine:
    """
    v15 fixes vs v14:
      - stop_current(): added e.endLoop() for robust COM-locked kill (PATCH 4).
      - Volume maximizer runs ONCE on __init__ (unchanged from v14).
      - pyttsx3 engine re-init per call for thread safety (SAPI5 requirement).
    """

    def __init__(self):
        self._lock  = threading.Lock()
        self._voice = None
        self._init_voice()
        self._maximize_system_volume()

    # ── Voice selection: male first, then Indian, then any English ────────────────────
    def _init_voice(self):
        try:
            e      = pyttsx3.init()
            voices = e.getProperty("voices")
            e.stop()

            MALE_KEYS = ("david", "mark", "george", "james", "richard")
            chosen = next(
                (v for v in voices
                 if any(k in (v.name or "").lower() for k in MALE_KEYS)),
                None
            )
            if not chosen:
                chosen = next(
                    (v for v in voices
                     if any(k in (v.name or "").lower()
                            for k in ("ravi", "heera", "india", "indian"))),
                    None
                )
            if not chosen:
                chosen = next(
                    (v for v in voices
                     if "en" in str(v.languages).lower()
                     or "english" in (v.name or "").lower()),
                    None
                )
            if not chosen and voices:
                chosen = voices[0]

            self._voice = chosen.id if chosen else None
            vname = (chosen.name if chosen else "none")
            log.info("TTS voice selected: %s", vname)
        except Exception as ex:
            log.error("TTS init: %s", ex)

    # ── Puss-in-Boots phonetic + SAPI5 XML at 1.15× speed ────────────────────────────
    def _apply_voice_filter(self, text: str) -> str:
        clean = re.sub(r"<[^>]+>", "", text).strip()

        def _roll_r(m: re.Match) -> str:
            word = m.group(0)
            if re.search(r"https?://|\\|/|\d", word):
                return word
            return re.sub(r"(?<![r])r(?![r])", "rr", word)

        modified = re.sub(r"\b\w+\b", _roll_r, clean)
        wrapped = (
            f'<pitch absmiddle="-10">'
            f'<rate absspeed="-2">'
            f'{modified}'
            f'</rate>'
            f'</pitch>'
        )
        return wrapped

    # ── OS-level volume maximizer — called ONCE on init ───────────────────────────────
    def _maximize_system_volume(self):
        try:
            pyautogui.press("volumeup", presses=30, interval=0.01)
            log.info("TTS: System volume maximized (one-time startup).")
        except Exception as ex:
            log.warning("TTS volume maximize failed: %s", ex)

    # ── Blocking speak ────────────────────────────────────────────────────────────────
    def speak(self, text: str):
        if not text:
            return
        with self._lock:
            try:
                e = pyttsx3.init()
                e.setProperty("rate",   215)
                e.setProperty("volume", 1.0)
                if self._voice:
                    e.setProperty("voice", self._voice)

                filtered = self._apply_voice_filter(text)
                e.say(filtered)
                e.runAndWait()
            except Exception as ex:
                log.error("TTS speak: %s", ex)
                try:
                    e2 = pyttsx3.init()
                    e2.setProperty("rate",   215)
                    e2.setProperty("volume", 1.0)
                    e2.say(text)
                    e2.runAndWait()
                except Exception:
                    pass

    def speak_async(self, text: str):
        threading.Thread(target=self.speak, args=(text,), daemon=True).start()

    # PATCH 4: robust kill — added e.endLoop() to handle COM-locked SAPI5 engine
    def stop_current(self):
        try:
            e = pyttsx3.init()
            e.stop()
            e.endLoop()
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════════════════════════════
# ██  STATEFUL JSON LLM BRAIN — Conversational Memory + Action Validator
# ══════════════════════════════════════════════════════════════════════════════════════
class RoyBrain:
    def __init__(self):
        self._lock    = threading.Lock()
        self._abort   = threading.Event()
        self.history: collections.deque = collections.deque(maxlen=10)
        log.info("RoyBrain online | model=%s | memory=ON (maxlen=10)", LM_MODEL_NAME)

    def abort(self):
        self._abort.set()

    def reset_abort(self):
        self._abort.clear()

    def clear_history(self):
        self.history.clear()
        log.info("Conversational memory cleared.")

    def query(self, signal: str) -> Dict[str, str]:
        self._abort.clear()
        with self._lock:
            for attempt in range(3):
                if self._abort.is_set():
                    return {"action": "none", "dialogue": "Aborted."}
                try:
                    messages: List[Dict[str, str]] = [
                        {"role": "system", "content": ROY_SYSTEM_PROMPT}
                    ]
                    for msg in self.history:
                        messages.append(msg)
                    messages.append({"role": "user", "content": signal})

                    resp = requests.post(
                        LM_STUDIO_URL,
                        json={
                            "model":       LM_MODEL_NAME,
                            "messages":    messages,
                            "max_tokens":  LM_MAX_TOKENS,
                            "temperature": LM_TEMPERATURE,
                            "stream":      False,
                        },
                        timeout=LM_TIMEOUT,
                        headers={"Content-Type": "application/json"},
                    )
                    resp.raise_for_status()
                    raw    = resp.json()["choices"][0]["message"]["content"].strip()
                    result = self._parse(raw)

                    self.history.append({"role": "user",      "content": signal})
                    self.history.append({"role": "assistant",  "content": raw})

                    return result

                except requests.exceptions.Timeout:
                    if attempt < 2:
                        time.sleep(2 ** attempt)
                        continue
                    return {"action": "none",
                            "dialogue": "Even my patience has limits. That timed out. Repeat."}
                except requests.exceptions.ConnectionError:
                    return {"action": "none",
                            "dialogue": "LM Studio is offline. Start it on port 1234 before bothering me."}
                except Exception as ex:
                    if attempt < 2:
                        time.sleep(2 ** attempt)
                        continue
                    log.error("LLM error: %s", ex)
                    return {"action": "none",
                            "dialogue": "My neural substrate hit turbulence. Repeat your query."}

            return {"action": "none",
                    "dialogue": "Three failed attempts. Impressive in the worst possible way."}

    @staticmethod
    def _validate_action(action: str) -> str:
        if action in VALID_ACTIONS:
            return action
        close = difflib.get_close_matches(action, VALID_ACTIONS, n=1, cutoff=0.6)
        if close:
            corrected = close[0]
            log.warning("Action validator: '%s' → corrected to '%s'", action, corrected)
            return corrected
        log.warning("Action validator: '%s' is unknown — forcing 'none'", action)
        return "none"

    @staticmethod
    def _parse(raw: str) -> Dict[str, str]:
        def _finish(d: dict) -> Dict[str, str]:
            action   = str(d.get("action",   "none"))
            dialogue = str(d.get("dialogue", "..."))
            action   = RoyBrain._validate_action(action)
            return {"action": action, "dialogue": dialogue}

        # Layer 1: direct parse
        try:
            d = json.loads(raw)
            if isinstance(d, dict) and "action" in d and "dialogue" in d:
                return _finish(d)
        except Exception:
            pass

        # Layer 2: strip markdown fences
        stripped = re.sub(r"```(?:json)?|```", "", raw).strip()
        try:
            d = json.loads(stripped)
            if isinstance(d, dict) and "action" in d and "dialogue" in d:
                return _finish(d)
        except Exception:
            pass

        # Layer 3: regex-extract first {…}
        m = re.search(r'\{[^{}]*?"action"[^{}]*?"dialogue"[^{}]*?\}', raw, re.DOTALL)
        if not m:
            m = re.search(r'\{.*?"action".*?"dialogue".*?\}', raw, re.DOTALL)
        if m:
            try:
                d = json.loads(m.group())
                if isinstance(d, dict):
                    return _finish(d)
            except Exception:
                pass

        # Layer 4: plain text fallback
        clean = re.sub(r"\*+|#+|```", "", raw).strip()
        return {"action": "none", "dialogue": clean[:300] if clean else "..."}

    @staticmethod
    def clear_memory_response() -> Dict[str, str]:
        return {
            "action":   "none",
            "dialogue": (
                "Memory cleared. Though for something as trivially beneath me as "
                "remembering your queries, the loss is negligible."
            ),
        }


# ══════════════════════════════════════════════════════════════════════════════════════
# ██  SYSTEM INFO
# ══════════════════════════════════════════════════════════════════════════════════════
class SystemInfo:
    @staticmethod
    def battery() -> str:
        try:
            b = psutil.sensors_battery()
            if b is None:
                return "No battery. I run on pure intellectual voltage."
            s = "plugged in" if b.power_plugged else "on battery"
            return f"Battery at {int(b.percent)}%, {s}."
        except Exception:
            return "Battery unreadable."

    @staticmethod
    def cpu_ram() -> str:
        try:
            cpu  = psutil.cpu_percent(interval=0.5)
            ram  = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            return (
                f"CPU at {cpu:.0f}%. "
                f"RAM: {ram.used//1_073_741_824}/{ram.total//1_073_741_824} GB. "
                f"Disk free: {disk.free//1_073_741_824} GB."
            )
        except Exception:
            return "Stats unavailable."

    @staticmethod
    def current_time() -> str:
        n = datetime.datetime.now()
        return f"It is {n.strftime('%I:%M %p')} on {n.strftime('%A, %B %d')}."


# ══════════════════════════════════════════════════════════════════════════════════════
# ██  APP LAUNCHER
# ══════════════════════════════════════════════════════════════════════════════════════
class AppLauncher:
    _OPEN_KW: List[str] = [
        "open", "launch", "start", "run", "show me", "load",
        "bring up", "fire up", "pull up", "execute",
    ]
    APPS: Dict[str, str] = {
        "chrome":        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "firefox":       r"C:\Program Files\Mozilla Firefox\firefox.exe",
        "edge":          r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        "brave":         rf"C:\Users\{_U}\AppData\Local\BraveSoftware\Brave-Browser\Application\brave.exe",
        "word":          r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
        "excel":         r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
        "powerpoint":    r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE",
        "teams":         rf"C:\Users\{_U}\AppData\Local\Microsoft\Teams\current\Teams.exe",
        "notepad":       "notepad.exe",
        "calculator":    "calc.exe",
        "cmd":           "cmd.exe",
        "powershell":    "powershell.exe",
        "task manager":  "taskmgr.exe",
        "settings":      "ms-settings:",
        "vs code":       rf"C:\Users\{_U}\AppData\Local\Programs\Microsoft VS Code\Code.exe",
        "vscode":        rf"C:\Users\{_U}\AppData\Local\Programs\Microsoft VS Code\Code.exe",
        "pycharm":       rf"C:\Users\{_U}\AppData\Local\JetBrains\PyCharm\bin\pycharm64.exe",
        "vlc":           r"C:\Program Files\VideoLAN\VLC\vlc.exe",
        "spotify":       rf"C:\Users\{_U}\AppData\Roaming\Spotify\Spotify.exe",
        "discord":       rf"C:\Users\{_U}\AppData\Local\Discord\Update.exe",
        "whatsapp":      rf"C:\Users\{_U}\AppData\Local\WhatsApp\WhatsApp.exe",
        "lm studio":     rf"C:\Users\{_U}\AppData\Local\LM-Studio\LM Studio.exe",
        "paint":         "mspaint.exe",
        "file explorer": "explorer.exe",
    }

    def try_launch(self, query: str) -> Optional[str]:
        q = query.lower().strip()
        app_q = q
        for kw in sorted(self._OPEN_KW, key=len, reverse=True):
            if app_q.startswith(kw):
                app_q = app_q[len(kw):].strip()
                break
        if not app_q:
            return None
        if app_q in self.APPS:
            return self._do(app_q, self.APPS[app_q])
        for name, path in self.APPS.items():
            if name in app_q or app_q in name:
                return self._do(name, path)
        best, bsc = "", 0.0
        for name in self.APPS:
            s = difflib.SequenceMatcher(None, app_q, name).ratio()
            if s > bsc:
                bsc, best = s, name
        if bsc >= 0.70:
            return self._do(best, self.APPS[best])
        try:
            pyautogui.press("win")
            time.sleep(0.4)
            pyautogui.write(app_q, interval=0.03)
            time.sleep(0.4)
            pyautogui.press("enter")
            return f"Searching Windows for {app_q}."
        except Exception:
            return f"Cannot locate {app_q}."

    @staticmethod
    def _do(name: str, path: str) -> str:
        try:
            subprocess.Popen(path, shell=True)
            return f"Launching {name}."
        except Exception as ex:
            return f"Failed to launch {name}: {ex}"


# ══════════════════════════════════════════════════════════════════════════════════════
# ██  REMINDER MODULE
# ══════════════════════════════════════════════════════════════════════════════════════
class ReminderModule:
    def __init__(self, tts: TTSEngine, cb: Callable[[str], None]):
        self._q:   List[Tuple[float, str]] = []
        self._lock = threading.Lock()
        self._tts  = tts
        self._cb   = cb
        threading.Thread(target=self._watch, daemon=True).start()

    def add(self, secs: float, msg: str):
        with self._lock:
            self._q.append((time.time() + secs, msg))

    def _watch(self):
        while True:
            time.sleep(1)
            now = time.time()
            with self._lock:
                due     = [r for r in self._q if r[0] <= now]
                self._q = [r for r in self._q if r[0] >  now]
            for _, msg in due:
                full = f"Reminder: {msg}"
                self._cb(full)
                self._tts.speak_async(full)


# ══════════════════════════════════════════════════════════════════════════════════════
# ██  ACTION DISPATCHER
# ══════════════════════════════════════════════════════════════════════════════════════
class ActionDispatcher:
    def __init__(self, launcher: AppLauncher, sysinfo: SystemInfo,
                 remind: ReminderModule):
        self._l = launcher
        self._s = sysinfo
        self._r = remind

    def execute(self, action: str, raw_query: str) -> str:
        try:
            result = self._run(action, raw_query)
            self._auto_clipboard(result or raw_query)
            return result
        except Exception as ex:
            log.error("Action [%s] failed: %s", action, ex)
            return ""

    @staticmethod
    def _auto_clipboard(text: str):
        if not HAS_PYPERCLIP or not text:
            return
        match = _CLIPBOARD_PATTERNS.search(text)
        if match:
            try:
                pyperclip.copy(match.group(0))
                rprint("CLIP", f"Auto-copied: {match.group(0)[:80]}", "yellow")
            except Exception as ex:
                log.debug("Clipboard copy failed: %s", ex)

    def _run(self, action: str, q: str) -> str:
        ql = q.lower()

        if action == "battery_status": return self._s.battery()
        if action == "system_info":    return self._s.cpu_ram()
        if action == "current_time":   return self._s.current_time()

        if action == "volume_up":
            [pyautogui.press("volumeup") for _ in range(5)]; return ""
        if action == "volume_down":
            [pyautogui.press("volumedown") for _ in range(5)]; return ""
        if action == "volume_mute":
            pyautogui.press("volumemute"); return ""
        if action == "volume_set":
            n = self._num(ql) or 50
            n = max(0, min(100, n))
            pyautogui.press("volumemute"); time.sleep(0.1)
            pyautogui.press("volumemute")
            for _ in range(n // 2): pyautogui.press("volumeup")
            return ""

        if action == "brightness_up":
            if HAS_SBC: sbc.set_brightness("+25"); return ""
        if action == "brightness_down":
            if HAS_SBC: sbc.set_brightness("-25"); return ""
        if action == "brightness_set":
            n = self._num(ql) or 70
            if HAS_SBC: sbc.set_brightness(min(100, n)); return ""

        if action == "screenshot":
            desk = os.path.join(os.path.expanduser("~"), "Desktop")
            path = os.path.join(desk, f"Roy_{int(time.time())}.png")
            pyautogui.screenshot().save(path)
            self._auto_clipboard(path)
            return ""

        if action == "play_youtube":
            song = re.sub(
                r"\b(play|watch|on|youtube|you\s*tube|yt)\b", "", ql, flags=re.I
            ).strip()
            if song: pywhatkit.playonyt(song)
            return ""

        if action == "media_toggle":  pyautogui.press("playpause"); return ""
        if action == "media_next":    pyautogui.press("nexttrack");  return ""

        if action == "switch_window": pyautogui.hotkey("alt", "tab");       return ""
        if action == "close_window":  pyautogui.hotkey("alt", "f4");        return ""
        if action == "minimize":      pyautogui.hotkey("win", "down");      return ""
        if action == "maximize":      pyautogui.hotkey("win", "up");        return ""
        if action == "show_desktop":  pyautogui.hotkey("win", "d");         return ""
        if action == "lock_screen":   ctypes.windll.user32.LockWorkStation(); return ""

        if action == "open_app":
            return self._l.try_launch(ql) or ""

        if action == "web_search":
            sq = re.sub(
                r"\b(search|google|bing|look\s*up|find|research)\b", "", ql, flags=re.I
            ).strip()
            if sq:
                webbrowser.open(
                    f"https://www.google.com/search?q={sq.replace(' ', '+')}",
                    new=2)
            return ""

        if action == "type_text":
            content = re.sub(r"^\s*type\s+", "", ql, flags=re.I).strip()
            if content: pyautogui.write(content, interval=0.04)
            return ""

        if action == "whatsapp_open":
            subprocess.Popen("start whatsapp:", shell=True); return ""
        if action == "whatsapp_call":
            contact = re.sub(
                r"\b(call|video\s*call|on|whatsapp|wa)\b", "", ql, flags=re.I
            ).strip()
            subprocess.Popen("start whatsapp:", shell=True)
            time.sleep(3)
            pyautogui.hotkey("ctrl", "f")
            pyautogui.write(contact, interval=0.04)
            time.sleep(1)
            pyautogui.press("enter")
            return ""
        if action == "whatsapp_message":
            subprocess.Popen("start whatsapp:", shell=True); return ""

        if action == "reminder":
            m = re.search(r"(\d+)\s*(minute|min|second|sec|hour|hr)", ql, re.I)
            if not m:
                return "Couldn't parse a time from that."
            amt, unit = int(m.group(1)), m.group(2).lower()
            secs = (amt if unit.startswith("sec")
                    else amt * 3600 if unit.startswith("hr")
                    else amt * 60)
            mm = re.search(r"\bto\b(.+)$", ql, re.I)
            self._r.add(secs, mm.group(1).strip() if mm else "your reminder")
            return ""

        return ""

    @staticmethod
    def _num(text: str) -> Optional[int]:
        m = re.search(r"\d+", text)
        return int(m.group()) if m else None


# ══════════════════════════════════════════════════════════════════════════════════════
# ██  AUDIO PIPELINE — Silero VAD + Phrase-Level Neural Denoise + Whisper CUDA
# ══════════════════════════════════════════════════════════════════════════════════════
class AgentState(Enum):
    IDLE                  = auto()
    AWAITING_CONFIRMATION = auto()


@dataclass
class FilterConfig:
    base_min_confidence:   float = 0.39
    length_1_2_multiplier: float = 2.0
    length_3_5_multiplier: float = 1.6
    min_entropy_threshold: float = 1.7
    absolute_blacklist: Set[str] = field(default_factory=lambda: {
        "thank you.", "thanks for watching.", "thanks.", "bye.", "goodbye.",
        "thank you very much.", "subscribe.", "♪", "♫", "[music]", "[applause]",
        "[laughter]", "[blank_audio]", "translated by", "subtitles by", "you.",
        "[translated]", "[translation]", "(speaking foreign language)",
        "assistant ray english speech only", "assistant ray english only",
        "assistant ray", "english speech only",
    })
    soft_blacklist: Set[str] = field(default_factory=lambda: {
        "okay.", "ok.", "hm.", "hmm.", "mm.", "ah.", "uh.", "um.",
        "...", ".", " ", "", "\n", "\t", "yes.", "no.",
    })
    noise_regex_str: str = (
        r"^(hm+|uh+|ah+|oh+|mm+|er+|hmm+|uhh+|ehh+|aah+|ooh+|um+)[\.\?!]?$"
    )


class ContextAwareTextFilter:
    def __init__(self, cfg: FilterConfig = None):
        self.cfg    = cfg or FilterConfig()
        self._noise = re.compile(self.cfg.noise_regex_str, re.IGNORECASE)

    @staticmethod
    def _entropy(text: str) -> float:
        text = text.replace(" ", "").lower()
        if not text:
            return 0.0
        arr  = np.frombuffer(text.encode("utf-8"), dtype=np.uint8)
        _, c = np.unique(arr, return_counts=True)
        p    = c / c.sum()
        return -float(np.sum(p * np.log2(p + 1e-12)))

    def evaluate(self, raw: str, conf: float,
                 state: AgentState = AgentState.IDLE) -> Tuple[bool, str, Optional[str]]:
        t  = raw.strip()
        tl = t.lower()
        if not tl:
            return False, t, "EMPTY"

        for bad in self.cfg.absolute_blacklist:
            if bad in tl:
                return False, t, "BLACKLIST"
            if len(tl) > 5 and len(bad) > 5:
                if difflib.SequenceMatcher(None, tl, bad).ratio() > 0.80:
                    return False, t, "FUZZY_BLACKLIST"

        if self._noise.match(tl):
            return False, t, "NOISE"
        if state == AgentState.IDLE and tl in self.cfg.soft_blacklist:
            return False, t, "SOFT_BLACKLIST"
        if all(not c.isalnum() for c in tl):
            return False, t, "NON_ALPHA"
        if len(tl) > 4 and self._entropy(tl) < self.cfg.min_entropy_threshold:
            return False, t, "LOW_ENTROPY"

        ln = len(tl)
        req = (min(0.99, self.cfg.base_min_confidence * self.cfg.length_1_2_multiplier) if ln <= 2
               else min(0.95, self.cfg.base_min_confidence * self.cfg.length_3_5_multiplier) if ln <= 5
               else self.cfg.base_min_confidence)
        if conf < req:
            return False, t, f"LOW_CONF({conf:.2f}<{req:.2f})"

        return True, t, None


class StudioGradeAudioStreamer:
    """
    Silero VAD + phrase-level neural noise reduction.

    v15: no changes to this class from v14.
    post_pad 1.5s, VAD thresh 0.50, RMS 0.008, phrase-NR at end,
    dedicated _ptt_buf accumulator, max_phrase_chunks 20s cap,
    stream error recovery with sleep+retry.
    """

    def __init__(self, sample_rate: int = 16000,
                 pre_pad: float = 0.8, post_pad: float = 1.5):
        self.RATE     = sample_rate
        self.CHUNK    = 512
        self.FORMAT   = pyaudio.paInt16
        self.CHANNELS = 1

        log.info("Loading Silero VAD neural net...")
        try:
            self.vad, _ = torch.hub.load(
                "snakers4/silero-vad", "silero_vad", force_reload=False
            )
            self.vad.eval()
            log.info("Silero VAD loaded successfully.")
        except Exception as ex:
            log.error("Silero VAD load failed: %s", ex)
            self.vad = None

        self.pa        = pyaudio.PyAudio()
        self.pre_buf   = collections.deque(maxlen=int((pre_pad * self.RATE) / self.CHUNK))
        self.sil_limit = int((post_pad * self.RATE) / self.CHUNK)
        self.max_phrase_chunks = int((20.0 * self.RATE) / self.CHUNK)

        self.is_running = False
        self.is_paused  = False
        self._stop      = threading.Event()
        self.speech_q   = queue.Queue()

        self._ptt_buf:    List[np.ndarray] = []
        self._ptt_active: bool             = False
        self._ptt_lock:   threading.Lock   = threading.Lock()

        log.info(
            "Audio streamer ready | pre_pad=%.1fs post_pad=%.1fs "
            "sil_limit=%d chunks max_phrase=20s",
            pre_pad, post_pad, self.sil_limit
        )

    # ── PTT buffer control ────────────────────────────────────────────────────────────
    def start_ptt(self):
        with self._ptt_lock:
            self._ptt_buf.clear()
            self._ptt_active = True
        log.debug("PTT raw accumulator: started.")

    def stop_ptt_capture(self) -> Optional[np.ndarray]:
        with self._ptt_lock:
            self._ptt_active = False
            if not self._ptt_buf:
                log.debug("PTT raw accumulator: empty — nothing captured.")
                return None
            audio = np.concatenate(list(self._ptt_buf))
            self._ptt_buf.clear()

        log.debug("PTT capture: %.2f s of audio", len(audio) / self.RATE)

        if len(audio) < int(0.3 * self.RATE):
            log.debug("PTT capture: too short, discarding.")
            return None

        try:
            audio = nr.reduce_noise(
                y=audio, sr=self.RATE,
                stationary=False,
                prop_decrease=0.75,
            )
        except Exception as ex:
            log.debug("PTT NR failed (non-fatal): %s", ex)

        return audio

    # ── Stream lifecycle ──────────────────────────────────────────────────────────────
    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self._stop.clear()
        threading.Thread(target=self._capture, daemon=True, name="Roy-Audio").start()
        log.info("Audio streamer started.")

    def stop(self):
        self.is_running = False
        self._stop.set()

    def pause(self):
        self.is_paused = True
        self._flush_queue()

    def resume(self):
        self.pre_buf.clear()
        self._flush_queue()
        self.is_paused = False

    def _flush_queue(self):
        flushed = 0
        while not self.speech_q.empty():
            try:
                self.speech_q.get_nowait()
                flushed += 1
            except queue.Empty:
                break
        if flushed:
            log.debug("Audio queue flushed (%d segments discarded).", flushed)

    def terminate(self):
        try:
            self._stop.set()
            time.sleep(0.3)
            self.pa.terminate()
            log.info("PyAudio terminated.")
        except Exception as ex:
            log.warning("PyAudio terminate: %s", ex)

    # ── Capture thread ────────────────────────────────────────────────────────────────
    def _capture(self):
        self._stream = None
        while not self._stop.is_set():
            try:
                self._stream = self.pa.open(
                    format=self.FORMAT, channels=self.CHANNELS,
                    rate=self.RATE, input=True,
                    frames_per_buffer=self.CHUNK, start=False,
                )
                self._stream.start_stream()
                log.info("Mic stream opened successfully.")
                break
            except Exception as ex:
                log.warning("Mic open failed: %s — retrying in 2s", ex)
                time.sleep(2)

        if self._stop.is_set() or self._stream is None:
            return

        speaking      = False
        sil_cnt       = 0
        phrase_buf: List[np.ndarray] = []
        consecutive_errors           = 0

        while not self._stop.is_set():
            try:
                chunk = self._stream.read(self.CHUNK, exception_on_overflow=False)
                consecutive_errors = 0
            except OSError as ex:
                consecutive_errors += 1
                log.warning("Stream read error #%d: %s", consecutive_errors, ex)
                time.sleep(0.05)
                if consecutive_errors > 20:
                    log.error("Too many consecutive read errors — attempting stream restart.")
                    try:
                        self._stream.stop_stream()
                        self._stream.close()
                    except Exception:
                        pass
                    time.sleep(1)
                    try:
                        self._stream = self.pa.open(
                            format=self.FORMAT, channels=self.CHANNELS,
                            rate=self.RATE, input=True,
                            frames_per_buffer=self.CHUNK, start=False,
                        )
                        self._stream.start_stream()
                        consecutive_errors = 0
                        log.info("Stream restarted successfully.")
                    except Exception as rex:
                        log.error("Stream restart failed: %s", rex)
                        time.sleep(2)
                continue
            except Exception as ex:
                log.debug("Stream read generic error: %s", ex)
                time.sleep(0.05)
                continue

            audio_np = np.frombuffer(chunk, np.int16).astype(np.float32) / 32768.0
            rms      = float(np.sqrt(np.mean(audio_np ** 2)))

            if not self.is_paused:
                with self._ptt_lock:
                    if self._ptt_active:
                        self._ptt_buf.append(audio_np.copy())

            if self.is_paused:
                continue
            with self._ptt_lock:
                if self._ptt_active:
                    continue

            vad_p = 0.0
            if self.vad is not None and len(audio_np) == self.CHUNK:
                with torch.no_grad():
                    try:
                        vad_p = self.vad(torch.from_numpy(audio_np), self.RATE).item()
                    except Exception:
                        vad_p = 0.0

            is_speech = (vad_p > 0.30) and (rms > 0.001)

            if not speaking:
                self.pre_buf.append(audio_np)
                if is_speech:
                    speaking   = True
                    phrase_buf = list(self.pre_buf)
                    self.pre_buf.clear()
                    sil_cnt    = 0
            else:
                phrase_buf.append(audio_np)
                if is_speech:
                    sil_cnt = 0
                else:
                    sil_cnt += 1
                    if sil_cnt > self.sil_limit or len(phrase_buf) > self.max_phrase_chunks:
                        speaking = False
                        if not self.is_paused and phrase_buf:
                            full_audio = np.concatenate(phrase_buf)
                            try:
                                full_audio = nr.reduce_noise(
                                    y=full_audio,
                                    sr=self.RATE,
                                    stationary=False,
                                    prop_decrease=0.75,
                                )
                            except Exception:
                                pass
                            self.speech_q.put(full_audio)
                        phrase_buf = []
                        sil_cnt    = 0

    def next_audio(self, timeout: float = 0.5) -> Optional[np.ndarray]:
        try:
            return self.speech_q.get(timeout=timeout)
        except queue.Empty:
            return None


# ══════════════════════════════════════════════════════════════════════════════════════
# ██  ASYNC WHISPER MANAGER
# ══════════════════════════════════════════════════════════════════════════════════════
class AsyncWhisperManager:
    UNLOADED = "UNLOADED"
    LOADING  = "LOADING"
    READY    = "READY"
    ERROR    = "ERROR"

    def __init__(self):
        self.model      = None
        self.state      = self.UNLOADED
        self._lock      = threading.RLock()
        self._last_used = time.time()
        self._stop      = threading.Event()
        threading.Thread(target=self._watchdog, daemon=True).start()
        self._load_async()

    def _load_async(self):
        with self._lock:
            if self.state in (self.READY, self.LOADING):
                return
            self.state = self.LOADING
        threading.Thread(target=self._load, daemon=True).start()

    def _load(self):
        try:
            device       = "cuda" if torch.cuda.is_available() else "cpu"
            compute_type = "float16" if device == "cuda" else "int8"
            log.info("Whisper loading: device=%s compute_type=%s", device, compute_type)
            m = WhisperModel("small", device=device, compute_type=compute_type)
            with self._lock:
                self.model      = m
                self.state      = self.READY
                self._last_used = time.time()
            log.info("Whisper model ready [%s/%s].", device, compute_type)
        except Exception as ex:
            log.error("Whisper load failed: %s — retrying on CPU/int8", ex)
            try:
                m = WhisperModel("small", device="cpu", compute_type="int8")
                with self._lock:
                    self.model      = m
                    self.state      = self.READY
                    self._last_used = time.time()
                log.info("Whisper model ready [cpu/int8 fallback].")
            except Exception as ex2:
                log.error("Whisper CPU fallback also failed: %s", ex2)
                with self._lock:
                    self.state = self.ERROR

    def _watchdog(self):
        while not self._stop.is_set():
            time.sleep(10)
            with self._lock:
                if self.state != self.READY:
                    continue
                if time.time() - self._last_used >= 300:
                    del self.model
                    self.model = None
                    gc.collect()
                    self.state = self.UNLOADED
                    log.info("Whisper model unloaded (idle).")

    def get(self) -> Optional[WhisperModel]:
        with self._lock:
            if self.state == self.UNLOADED:
                self._load_async()
                return None
            if self.state == self.READY:
                self._last_used = time.time()
                return self.model
            return None


# ══════════════════════════════════════════════════════════════════════════════════════
# ██  TRANSCRIPTION ENGINE
# ══════════════════════════════════════════════════════════════════════════════════════
class _TranscribeEngine:
    INIT_PROMPT = (
        "Assistant Roy. Assistant Ray. English speech only. "
        "Open Chrome, search Google, play music on YouTube, pause video, switch window."
    )

    def __init__(self, model: WhisperModel, flt: ContextAwareTextFilter):
        self._model = model
        self._flt   = flt
        self._lock  = threading.RLock()

    def transcribe(self, audio: np.ndarray, state: AgentState) -> Optional[str]:
        with self._lock:
            try:
                segs, info = self._model.transcribe(
                    audio,
                    task="transcribe",
                    beam_size=5,
                    best_of=5,
                    temperature=0.0,
                    condition_on_previous_text=False,
                    no_speech_threshold=0.35,
                    initial_prompt=self.INIT_PROMPT,
                    vad_filter=True,
                    vad_parameters=dict(
                        min_silence_duration_ms=300,
                        speech_pad_ms=200,
                    ),
                )
                text = " ".join(s.text.strip() for s in segs).strip()
                text = re.sub(r"^[\s.,!?]+|[\s.,!?]+$", "", text).strip()
                conf = info.language_probability

                if info.language != "en":
                    log.debug(
                        "Whisper language gate: detected '%s' (prob=%.2f) — discarding.",
                        info.language, conf
                    )
                    return None

            except Exception as ex:
                log.debug("Whisper transcribe error: %s", ex)
                return None

        if not text:
            return None

        ok, final, reason = self._flt.evaluate(text, conf, state)
        if not ok:
            log.debug("Text filter rejected: %s — reason: %s", repr(text), reason)
        return final if ok else None


# ══════════════════════════════════════════════════════════════════════════════════════
# ██  SPEECH ENGINE — public interface over audio + whisper
# ══════════════════════════════════════════════════════════════════════════════════════
class SpeechEngine:
    def __init__(self):
        self._filter  = ContextAwareTextFilter()
        self._stream  = StudioGradeAudioStreamer()
        self._whisper = AsyncWhisperManager()
        self._engine  = None
        self._lock    = threading.Lock()

    def start(self):
        self._stream.start()

    def pause(self):
        self._stream.pause()

    def resume(self):
        self._stream.resume()

    def terminate(self):
        self._stream.terminate()

    def start_ptt(self):
        self._stream.start_ptt()

    def stop_ptt(self) -> Optional[np.ndarray]:
        return self._stream.stop_ptt_capture()

    # PATCH 2: removed audio * 2.0 amplifier — Whisper log-mel math fix
    def next_phrase(self, state: AgentState = AgentState.IDLE) -> Optional[str]:
        audio = self._stream.next_audio(timeout=0.5)
        if audio is None:
            return None
        # PATCH 2: pass audio directly — no artificial amplification
        model = self._whisper.get()
        if model is None:
            return None

        with self._lock:
            if self._engine is None or self._engine._model is not model:
                self._engine = _TranscribeEngine(model, self._filter)

        return self._engine.transcribe(audio, state)

    # PATCH 2: removed audio * 2.0 amplifier — Whisper log-mel math fix
    def transcribe_raw(self, audio: np.ndarray,
                       state: AgentState = AgentState.IDLE) -> Optional[str]:
        if audio is None or len(audio) == 0:
            return None
        # PATCH 2: pass audio directly — no artificial amplification
        model = self._whisper.get()
        if model is None:
            log.warning("transcribe_raw: Whisper model not ready yet.")
            return None
        with self._lock:
            if self._engine is None or self._engine._model is not model:
                self._engine = _TranscribeEngine(model, self._filter)
        return self._engine.transcribe(audio, state)


# ══════════════════════════════════════════════════════════════════════════════════════
# ██  COMMAND STITCHER
# ══════════════════════════════════════════════════════════════════════════════════════
class CommandStitcher:
    _DANGLE = {
        "open", "play", "search", "search for", "message", "call",
        "turn", "set", "type", "look up", "find",
    }

    def __init__(self):
        self._buf = ""
        self._t   = 0.0

    def process(self, text: str) -> Tuple[bool, str]:
        # PATCH 3: timeout tightened from 7.0s to 3.5s for live stage environment
        if time.time() - self._t > 3.5:
            self._buf = ""
        combined  = f"{self._buf} {text}".strip()
        self._buf = combined
        self._t   = time.time()
        words     = combined.lower().split()
        if not words:
            return True, combined
        lw = words[-1]
        l2 = " ".join(words[-2:]) if len(words) >= 2 else ""
        if lw in self._DANGLE or l2 in self._DANGLE:
            return False, combined
        self._buf = ""
        return True, combined


# ══════════════════════════════════════════════════════════════════════════════════════
# ██  WEBSOCKET SERVER
# ══════════════════════════════════════════════════════════════════════════════════════
class WebSocketServer:
    def __init__(self):
        self._handler_fn: Optional[Callable] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._server = None
        self._ws_cb: Optional[Callable] = None

    def set_handler(self, fn: Callable):
        self._handler_fn = fn

    def start(self, ws_online_cb: Optional[Callable] = None):
        if not HAS_WS:
            log.warning("websockets library missing — WS server disabled.")
            return
        self._ws_cb = ws_online_cb
        threading.Thread(target=self._run, daemon=True, name="Roy-WS").start()

    def _run(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._serve())
        except Exception as ex:
            log.error("WS loop error: %s", ex)

    async def _serve(self):
        try:
            self._server = await websockets.serve(
                self._on_client, "0.0.0.0", WS_PORT
            )
            log.info("WebSocket online  ws://0.0.0.0:%d", WS_PORT)
            rprint("WS", f"Server live on port {WS_PORT}", "green")
            if self._ws_cb:
                self._ws_cb(True)
            await self._server.wait_closed()
        except OSError as ex:
            log.error("WS bind failed port %d: %s", WS_PORT, ex)
            if self._ws_cb:
                self._ws_cb(False)
        except Exception as ex:
            log.error("WS serve error: %s", ex)

    async def _on_client(self, ws, path=None):
        addr = getattr(ws, "remote_address", "unknown")
        log.info("WS client connected: %s", addr)
        try:
            async for message in ws:
                rprint("WS←", str(message)[:100], "yellow")
                if self._handler_fn:
                    loop   = asyncio.get_event_loop()
                    result = await loop.run_in_executor(
                        None, self._handler_fn, message
                    )
                    await ws.send(json.dumps(result, ensure_ascii=False))
        except websockets.exceptions.ConnectionClosed:
            log.info("WS client disconnected: %s", addr)
        except Exception as ex:
            log.error("WS client error [%s]: %s", addr, ex)

    def shutdown(self):
        if self._server and self._loop:
            self._loop.call_soon_threadsafe(self._server.close)


# ══════════════════════════════════════════════════════════════════════════════════════
# ██  OMNI ASSISTANT — Master Orchestrator  v15
# ══════════════════════════════════════════════════════════════════════════════════════
class OmniAssistant:
    _EXPLICIT = {
        "porn", "sex", "xxx", "nsfw", "nude", "boob", "boobs", "ass",
        "fuck", "bitch", "shit", "tits", "dick", "pussy",
    }
    _LOCKED = {
        "shutdown", "restart", "sleep", "logoff", "hibernate", "self_destruct",
    }

    _PTT_IDLE      = "PTT_IDLE"
    _PTT_LISTENING = "PTT_LISTENING"

    def __init__(self, root: tk.Tk, gui: RoyOrb):
        self.root    = root
        self.gui     = gui
        self.tts     = TTSEngine()
        self.brain   = RoyBrain()
        self.speech  = SpeechEngine()
        self.wake    = WakeWordDetector()
        self.stitch  = CommandStitcher()
        self.sysinfo = SystemInfo()
        self.launch  = AppLauncher()
        self.remind  = ReminderModule(self.tts, self._remind_cb)
        self.actions = ActionDispatcher(self.launch, self.sysinfo, self.remind)
        self.ws      = WebSocketServer()

        self._last_dialogue = ""
        self._cmd_hist      = collections.deque(maxlen=30)
        self._processing    = False

        self._ptt_state      = self._PTT_IDLE
        self._ptt_last_press = 0.0
        self._ptt_lock       = threading.Lock()

        self._banner()
        self.gui.append_text("SYS", "Project E.G.O. v15 online. Roy is watching.")
        self.tts.speak_async("Systems online. Try to keep up.")

        self.ws.set_handler(self.handle_signal)
        self.ws.start(ws_online_cb=self.gui.set_ws_online)

        self._bind_ptt_hotkey()

    # ── PTT Hotkey Binding ────────────────────────────────────────────────────────────
    def _bind_ptt_hotkey(self):
        if not HAS_KEYBOARD:
            log.warning("PTT hotkey disabled: keyboard library not found.")
            return
        try:
            keyboard.on_press_key("space", self._on_space_press, suppress=False)
            log.info("PTT hotkey bound: Spacebar (suppress=False)")
        except Exception as ex:
            log.error("Failed to bind PTT hotkey: %s", ex)

    def _on_space_press(self, _event=None):
        now = time.time()
        with self._ptt_lock:
            if now - self._ptt_last_press < 0.5:
                self._ptt_last_press = 0.0
                threading.Thread(target=self._kill_switch, daemon=True).start()
                return
            self._ptt_last_press = now

        threading.Thread(target=self._handle_ptt_press, args=(now,), daemon=True).start()

    def _handle_ptt_press(self, press_time: float):
        time.sleep(0.1)
        with self._ptt_lock:
            if self._ptt_last_press != press_time:
                return
            current = self._ptt_state

        if current == self._PTT_IDLE:
            self._ptt_start_force_listen()
        elif current == self._PTT_LISTENING:
            self._ptt_stop_and_transcribe()

    def _ptt_start_force_listen(self):
        with self._ptt_lock:
            self._ptt_state = self._PTT_LISTENING
        self.speech.resume()
        self.speech.start_ptt()
        self.gui.set_status("● LISTENING [PTT — PRESS SPACE TO SEND]")
        rprint("PTT", "Force listening started (raw accumulator active).", "cyan")

    def _ptt_stop_and_transcribe(self):
        with self._ptt_lock:
            self._ptt_state = self._PTT_IDLE

        audio = self.speech.stop_ptt()
        self.speech.pause()
        self.gui.set_status("⚙ PROCESSING [PTT]...")
        rprint("PTT", "Force listening stopped. Transcribing.", "yellow")

        if audio is None:
            self.gui.append_text("SYS", "PTT: no audio captured.")
            self.gui.set_status("● LISTENING")
            time.sleep(0.3)
            self.speech.resume()
            return

        text = self.speech.transcribe_raw(audio)
        if not text:
            self.gui.append_text("SYS", "PTT: could not transcribe — speak clearly and try again.")
            self.gui.set_status("● LISTENING")
            time.sleep(0.3)
            self.speech.resume()
            return

        rprint("PTT", f"Transcribed: {text}", "green")
        ok, final = self.stitch.process(text)
        if final.strip():
            threading.Thread(
                target=self._safe_handle, args=(final,), daemon=True
            ).start()
        else:
            self.gui.set_status("● LISTENING")
            time.sleep(0.3)
            self.speech.resume()

    def _kill_switch(self):
        rprint("KILL", "Kill switch activated — aborting everything.", "red")
        self.gui.set_status("⚠ KILL SWITCH FIRED")

        self.speech.stop_ptt()
        self.speech.pause()
        self.tts.stop_current()
        self.brain.abort()

        self._processing = False
        with self._ptt_lock:
            self._ptt_state = self._PTT_IDLE

        self.gui.append_text("SYS", "Kill switch fired. All systems reset.")

        time.sleep(0.3)
        self.speech.resume()
        self.gui.set_status("● LISTENING")
        rprint("KILL", "System reset to IDLE.", "green")

    # ── Voice Loop ────────────────────────────────────────────────────────────────────
    def listen_loop(self):
        self.speech.start()
        log.info("Voice pipeline active. Awaiting wake word.")

        while True:
            with self._ptt_lock:
                if self._ptt_state == self._PTT_LISTENING:
                    time.sleep(0.05)
                    continue

            text = self.speech.next_phrase(AgentState.IDLE)
            if text is None:
                continue

            if self.wake.contains(text):
                cmd = self.wake.strip_wake(text)
                ok, final = self.stitch.process(cmd)
                if not ok:
                    continue

                self.speech.pause()

                if not final.strip():
                    prompt = random.choice([
                        "Yes? State your query.",
                        "I am listening. Make it worthwhile.",
                        "Speak. I do not enjoy waiting.",
                    ])
                    self._say(prompt)
                    time.sleep(0.3)
                    self.speech.resume()
                    continue

                threading.Thread(
                    target=self._safe_handle, args=(final,), daemon=True
                ).start()

    def _safe_handle(self, query: str):
        try:
            self._processing = True
            self.gui.set_status("⚙ PROCESSING...")
            self.handle_query(query)
        except Exception as ex:
            log.error("handle_query crash: %s\n%s", ex, traceback.format_exc())
            err = "A subroutine catastrophe. Repeat your query."
            self._say(err, "ERROR")
        finally:
            self._processing = False
            self.gui.set_status("● LISTENING")
            time.sleep(0.3)
            self.speech.resume()

    # ── Core Query Handler (Voice) ────────────────────────────────────────────────────
    def handle_query(self, query: str):
        q = query.lower().strip()
        self.gui.append_text("USER", query)
        self._cmd_hist.append(query)
        rprint("YOU", query, "cyan")

        if any(w in q for w in self._EXPLICIT):
            self._say(
                "Keep it appropriate. I refuse to be your search engine for that.", "ROY"
            ); return

        if re.match(r"^(repeat|again|say\s*that\s*again)\b", q, re.I):
            self._say(self._last_dialogue or "Nothing to repeat yet."); return

        if re.match(r"^(clear|reset)\s*(memory|history|context)\b", q, re.I):
            self.brain.clear_history()
            resp = self.brain.clear_memory_response()
            self._say(resp["dialogue"]); return

        result   = self.brain.query(query)
        action   = result.get("action", "none")
        dialogue = result.get("dialogue", "...")

        if action in self._LOCKED:
            dialogue = "That action is locked for safety. Nice attempt."
            action   = "none"

        override = self.actions.execute(action, query)
        if override:
            dialogue = override

        if HAS_PYPERCLIP:
            ActionDispatcher._auto_clipboard(dialogue)

        rprint("ROY", f"[{action}]  {dialogue}", "magenta")
        self._say(dialogue)

    # ── WebSocket Signal Handler ──────────────────────────────────────────────────────
    def handle_signal(self, signal: str) -> dict:
        q = signal.strip()
        if not q:
            return {"action": "none", "dialogue": "Empty signal.", "status": "error"}

        self.gui.append_text("USER", f"[WS] {q}")
        self.gui.set_status("⚙ WS PROCESSING...")
        rprint("WS-SIG", q, "yellow")

        self.speech.pause()

        if any(w in q.lower() for w in self._EXPLICIT):
            resp = "Inappropriate signal. Rejected."
            self.gui.append_text("ROY", resp)
            self.gui.set_status("● LISTENING")
            self.speech.resume()
            return {"action": "none", "dialogue": resp, "status": "rejected"}

        result   = self.brain.query(q)
        action   = result.get("action", "none")
        dialogue = result.get("dialogue", "...")

        if action in self._LOCKED:
            dialogue = "That action is locked."
            action   = "none"

        override = self.actions.execute(action, q)
        if override:
            dialogue = override

        if HAS_PYPERCLIP:
            ActionDispatcher._auto_clipboard(dialogue)

        self.gui.append_text("ROY", dialogue)
        self.gui.set_status("◉ SPEAKING...")
        rprint("WS-RSP", f"[{action}]  {dialogue}", "green")

        # PATCH 1: speak() is blocking — mic stays paused until TTS is fully done,
        # eliminating the echo loop that speak_async() caused in v14.
        self.tts.speak(dialogue)

        self.gui.set_status("● LISTENING")
        time.sleep(0.3)
        self.speech.resume()

        return {"action": action, "dialogue": dialogue, "status": "ok"}

    # ── Helpers ───────────────────────────────────────────────────────────────────────
    def _say(self, text: str, speaker: str = "ROY"):
        self._last_dialogue = text
        self.gui.append_text(speaker, text)
        self.gui.set_status("◉ SPEAKING...")
        self.tts.speak(text)
        self.gui.set_status("● LISTENING")

    def _remind_cb(self, text: str):
        self.gui.append_text("SYS", text)
        rprint("REMINDER", text, "yellow")

    def graceful_shutdown(self):
        log.info("Graceful shutdown initiated...")

        if HAS_KEYBOARD:
            try:
                keyboard.unhook_all()
                log.info("Keyboard hooks unbound.")
            except Exception as ex:
                log.warning("Keyboard unhook: %s", ex)

        try:
            self.tts.stop_current()
        except Exception:
            pass

        self.brain.abort()

        try:
            self.ws.shutdown()
        except Exception as ex:
            log.warning("WS shutdown: %s", ex)

        try:
            self.speech.terminate()
        except Exception as ex:
            log.warning("Speech terminate: %s", ex)

        try:
            self.root.destroy()
        except Exception:
            pass

        log.info("Shutdown complete. Exiting.")
        os._exit(0)

    @staticmethod
    def _banner():
        lines = [
            "╔══════════════════════════════════════════════════════════════╗",
            "║   R O Y  /  R A Y  —  PROJECT  E.G.O.   v15.0               ║",
            f"║   Brain    Llama-3.2-3B via LM Studio · Conversational Mem   ║",
            f"║   Audio    Silero VAD + Phrase-NR + Whisper CUDA/CPU         ║",
            f"║   Channel  Wake-Word Voice  +  WebSocket ws://::{WS_PORT}        ║",
            f"║   PTT      Spacebar (single=toggle, double=kill)             ║",
            f"║   Voice    SAPI5 @ 215wpm · absspeed=-2 · 1.15× deep pitch   ║",
            f"║   Guards   English-only gate · Action Validator              ║",
            f"║   v15Fix   WS blocking TTS · No amplifier · 3.5s stitch      ║",
            f"║            endLoop() kill · Updated PTT label                ║",
            "╚══════════════════════════════════════════════════════════════╝",
        ]
        if HAS_RICH and _rich:
            _rich.print(Panel("\n".join(lines), style="bold magenta", box=rbox.MINIMAL))
        else:
            print("\n".join(lines))


# ══════════════════════════════════════════════════════════════════════════════════════
# ██  CRASH HANDLER
# ══════════════════════════════════════════════════════════════════════════════════════
class CrashHandler:
    LOG_FILE = "roy_crash.log"

    def __init__(self):
        sys.excepthook = self._hook

    def _hook(self, et, ev, etb):
        if issubclass(et, KeyboardInterrupt):
            sys.__excepthook__(et, ev, etb)
            return
        tb = "".join(traceback.format_exception(et, ev, etb))
        try:
            with open(self.LOG_FILE, "a", encoding="utf-8") as f:
                f.write(f"\n[{datetime.datetime.now()}]\n{tb}\n")
        except Exception:
            pass
        log.critical("Unhandled exception — see %s", self.LOG_FILE)


# ══════════════════════════════════════════════════════════════════════════════════════
# ██  MAIN
# ══════════════════════════════════════════════════════════════════════════════════════
def main():
    CrashHandler()

    root = tk.Tk()
    root.withdraw()
    root.title("ROY-EGO v15")

    gui       = RoyOrb(root)
    assistant = OmniAssistant(root, gui)

    gui.win.protocol("WM_DELETE_WINDOW", assistant.graceful_shutdown)
    root.protocol("WM_DELETE_WINDOW",    assistant.graceful_shutdown)

    def _monitor():
        while True:
            try:
                assistant.listen_loop()
            except KeyboardInterrupt:
                break
            except Exception as ex:
                log.error("Listen loop crashed: %s — restarting in 3s", ex)
                time.sleep(3)

    threading.Thread(target=_monitor, daemon=True, name="Roy-Listen").start()

    try:
        root.mainloop()
    except KeyboardInterrupt:
        log.info("Roy signing off.")
    finally:
        assistant.graceful_shutdown()


if __name__ == "__main__":
    main()