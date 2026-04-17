# ╔══════════════════════════════════════════════════════════════════════════════════════╗
# ║    R A Y  /  R O Y  —  ULTIMATE OMNI-AGENT  v7.9  ◈  EXPO APEX MONOLITH            ║
# ║    Active Window IQ + UI Watchdog + Fuzzy Hallucination Shield + Deep-VAD Denoise    ║
# ║    ─────────────────────────────────────────────────────────────────────────────     ║
# ║    100% self-contained — NO external local module imports.                           ║
# ║    Speech Engine (V7.9), Sleek Dash, Wake-Word, LLM, Commands — all fused here.      ║
# ╚══════════════════════════════════════════════════════════════════════════════════════╝

import collections
import ctypes
import datetime
import difflib
import gc
import io
import json
import logging
import math
import os
import queue
import random
import re
import struct
import subprocess
import sys
import threading
import time
import traceback
import unicodedata
import webbrowser
import winreg
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import numpy as np
import psutil
import pyaudio
import pyautogui
import pywhatkit
import pyttsx3
import requests
import tkinter as tk
from faster_whisper import WhisperModel
from tkinter import scrolledtext

# --- NEURAL AUDIO UPGRADES ---
import torch
import noisereduce as nr

try:
    import screen_brightness_control as sbc
    HAS_SBC = True
except Exception:
    HAS_SBC = False

try:
    import pystray
    from PIL import Image, ImageDraw
    HAS_TRAY = True
except Exception:
    HAS_TRAY = False

try:
    import win32clipboard
    HAS_CLIPBOARD = True
except Exception:
    HAS_CLIPBOARD = False

try:
    import winsound
    HAS_SOUND = True
except Exception:
    HAS_SOUND = False


# ══════════════════════════════════════════════════════════════════════════════
# ██  LOGGING
# ══════════════════════════════════════════════════════════════════════════════
class ColourFormatter(logging.Formatter):
    COLOURS = {
        logging.DEBUG:    "\033[36m",
        logging.INFO:     "\033[32m",
        logging.WARNING:  "\033[33m",
        logging.ERROR:    "\033[31m",
        logging.CRITICAL: "\033[35m",
    }
    RESET = "\033[0m"

    def format(self, record):
        colour = self.COLOURS.get(record.levelno, "")
        record.levelname = f"{colour}[{record.levelname}]{self.RESET}"
        return super().format(record)

def _setup_logger() -> logging.Logger:
    logger = logging.getLogger("RAY-EXPO")
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(ColourFormatter(
        fmt="%(asctime)s  %(levelname)s  %(message)s",
        datefmt="%H:%M:%S"
    ))
    logger.addHandler(handler)
    return logger

log = _setup_logger()


# ══════════════════════════════════════════════════════════════════════════════
# ██  ACTIVE WINDOW IQ (Context Awareness)
# ══════════════════════════════════════════════════════════════════════════════
def get_active_window_title() -> str:
    try:
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        buf = ctypes.create_unicode_buffer(length + 1)
        ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
        return buf.value if buf.value else "Desktop"
    except Exception:
        return "Desktop"


# ══════════════════════════════════════════════════════════════════════════════
# ██  CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════
LM_STUDIO_URL    = "http://localhost:1234/v1/chat/completions"
LM_MODEL_NAME    = "llama-3.2-3b-instruct"
LM_MAX_TOKENS    = 200
LM_TEMPERATURE   = 0.7  
LM_TIMEOUT       = 30   
CONV_HISTORY_LEN = 8

WAKE_WORD_MASTERS  = ["ray", "raye", "roy"]
WAKE_WORD_VARIANTS = [
    "ray", "raye", "rey", "reye", "rei", "rae", "wray", "rhey", "rhay", 
    "raa", "raay", "reigh", "raigh", "rayy", "reyy", "rrey",
    "roy", "roye", "roi", "roie", "roe", "rhoy", "rhoi", "rhoe", 
    "rooy", "royy", "ruy", "ruoy",
    "hey ray", "hi ray", "ok ray", "okay ray", "yo ray", "oi ray", "listen ray", "hello ray",
    "hey raye", "hi raye", "ok raye", "okay raye", "yo raye", "oi raye",
    "hey rey", "hi rey", "ok rey", "okay rey", "yo rey", "oi rey",
    "hey rei", "hi rei", "ok rei", "okay rei",
    "hey rae", "hi rae", "ok rae", "okay rae",
    "hey roy", "hi roy", "ok roy", "okay roy", "yo roy", "oi roy", "listen roy", "hello roy",
    "hey roi", "hi roi", "ok roi", "okay roi", "yo roi", "oi roi",
    "hey roe", "hi roe", "ok roe", "okay roe", 
    "ray ji", "roy ji", "rey ji", "roi ji",
    "ray bhai", "roy bhai", "rey bhai",
    "suno ray", "suno roy", "aur ray", "aur roy",
    "arey", "arrey", "aree", "arree",
    "hey ray ji", "hey roy ji", "ok ray ji", "ok roy ji"
]
WAKE_WORD_FUZZY_THRESHOLD = 0.72
_U = os.getenv("USERNAME", "User")


# ══════════════════════════════════════════════════════════════════════════════
# ██  COLOUR HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def _hex_to_rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def _lerp_colour(c1: str, c2: str, t: float) -> str:
    r1, g1, b1 = _hex_to_rgb(c1)
    r2, g2, b2 = _hex_to_rgb(c2)
    t = max(0.0, min(1.0, t))
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"

def create_round_rect(canvas, x1, y1, x2, y2, radius=15, **kwargs):
    points = [x1+radius, y1, x1+radius, y1, x2-radius, y1, x2-radius, y1, x2, y1,
              x2, y1+radius, x2, y1+radius, x2, y2-radius, x2, y2-radius, x2, y2,
              x2-radius, y2, x2-radius, y2, x1+radius, y2, x1+radius, y2, x1, y2,
              x1, y2-radius, x1, y2-radius, x1, y1+radius, x1, y1+radius, x1, y1]
    return canvas.create_polygon(points, **kwargs, smooth=True)


# ══════════════════════════════════════════════════════════════════════════════
# ██  THE HORIZONTAL DASHBOARD UI (EXPO EDITION) + WATCHDOG
# ══════════════════════════════════════════════════════════════════════════════
class RayRoyOverlay:
    def __init__(self, root: tk.Tk):
        self.root           = root
        self._alpha         = 0.0
        self._target_alpha  = 0.0
        self._idle_ticks    = 0
        self._thinking_ticks= 0  # UI Watchdog Counter
        self.phase          = 0.0  
        self._drag_x        = 0
        self._drag_y        = 0
        self._gui_lock      = threading.Lock()

        # Sleek Horizontal "Floating Pill"
        self.W = 850
        self.H = 160
        self.FPS = 30
        
        self.state = 'idle'
        self.particles = []
        self.wave_bars = []

        self.win = tk.Toplevel(root)
        self.win.withdraw()
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.attributes("-alpha", 0.0)
        self.win.configure(bg="#050810")

        # Center at the bottom of the screen perfectly
        sw = self.win.winfo_screenwidth()
        sh = self.win.winfo_screenheight()
        x  = (sw - self.W) // 2
        y  = sh - self.H - 60 
        self.win.geometry(f"{self.W}x{self.H}+{x}+{y}")

        self._init_data()
        self._build_ui()
        self._tick()

    def _init_data(self):
        bar_count = 30
        for i in range(bar_count):
            center = bar_count / 2
            dist = abs(i - center) / center
            hmin = int(3 + 3 * (1 - dist))
            hmax = int(6 + 28 * ((1 - dist) ** 1.5) * (0.8 + 0.2 * random.random()))
            self.wave_bars.append({
                'hmin': hmin, 'hmax': hmax, 
                'current_h': hmin, 'target_h': hmin,
                'delay_offset': (i / bar_count) * math.pi * 2
            })

    def _build_ui(self):
        self.canvas = tk.Canvas(self.win, width=self.W, height=self.H, bg="#050810", highlightthickness=0)
        self.canvas.place(x=0, y=0)
        self.canvas.bind("<ButtonPress-1>", self._drag_start)
        self.canvas.bind("<B1-Motion>", self._drag_motion)

        self.canvas.create_rectangle(1, 1, self.W-1, self.H-1, outline="#111628", width=2)
        
        CX_ORB = 125
        CY_ORB = 65

        self.canvas.create_oval(CX_ORB-80, CY_ORB-80, CX_ORB+80, CY_ORB+80, fill="#0a0f22", outline="")
        
        self.header_dot = self.canvas.create_oval(15, 12, 23, 20, fill="#3b5bff", outline="")
        self.canvas.create_text(32, 16, text="RAY OS v7.9", fill="#8888aa", font=("Inter", 9, "bold"), anchor="w")

        self.status_txt = self.canvas.create_text(CX_ORB, self.H - 20, text="READY TO LISTEN", fill="#555577", font=("Inter", 8, "bold"))

        self.orb_glow3 = self.canvas.create_oval(CX_ORB-45, CY_ORB-45, CX_ORB+45, CY_ORB+45, fill="#151b40", outline="")
        self.orb_glow2 = self.canvas.create_oval(CX_ORB-35, CY_ORB-35, CX_ORB+35, CY_ORB+35, fill="#2a2060", outline="")
        self.orb_shadow = self.canvas.create_oval(CX_ORB-25, CY_ORB-25, CX_ORB+25, CY_ORB+25, fill="#3b2fff", outline="")
        self.orb_main = self.canvas.create_oval(CX_ORB-18, CY_ORB-18, CX_ORB+18, CY_ORB+18, fill="#5577ff", outline="")
        self.orb_core = self.canvas.create_oval(CX_ORB-8, CY_ORB-8, CX_ORB+8, CY_ORB+8, fill="#88aaff", outline="")

        self.bar_ids = []
        bx_start = CX_ORB - (30 * 4) // 2
        by = CY_ORB + 55
        for i in range(30):
            x = bx_start + i * 5
            bid = self.canvas.create_rectangle(x, by, x+2, by, fill="#9f5fff", outline="")
            self.bar_ids.append(bid)

        self.canvas.create_line(250, 15, 250, self.H-15, fill="#111628", width=2)

        chat_x = 265
        chat_w = self.W - chat_x - 15
        
        self.chat = scrolledtext.ScrolledText(
            self.win, bg="#050810", fg="#cce8ff", bd=0, highlightthickness=0, 
            font=("Consolas", 10), wrap=tk.WORD, state="disabled"
        )
        self.chat.place(x=chat_x, y=15, width=chat_w, height=self.H-30)
        
        self.chat.tag_config("user_label", foreground="#00d4ff", font=("Consolas", 10, "bold"))
        self.chat.tag_config("ray_label", foreground="#ff4fcf", font=("Consolas", 10, "bold"))
        self.chat.tag_config("body", foreground="#8899bb")
        self.chat.tag_config("sys", foreground="#555577", font=("Consolas", 9, "italic"))

    def _drag_start(self, e):
        self._drag_x, self._drag_y = e.x, e.y

    def _drag_motion(self, e):
        dx = e.x - self._drag_x
        dy = e.y - self._drag_y
        self.win.geometry(f"+{self.win.winfo_x() + dx}+{self.win.winfo_y() + dy}")

    def append_text(self, speaker: str, text: str, kind: str = "body"):
        def _do():
            with self._gui_lock:
                self.chat.config(state="normal")
                spk = speaker.upper()
                if spk == "USER":
                    lbl, tag = "YOU", "user_label"
                elif spk == "AGENT":
                    lbl, tag = "RAY", "ray_label"
                elif spk == "ERROR":
                    lbl, tag = "ERR", "sys"
                else:
                    lbl, tag = "SYS", "sys"
                
                self.chat.insert(tk.END, f"\n {lbl}  ", tag)
                self.chat.insert(tk.END, f" {text}\n", "body")
                self.chat.yview(tk.END)  # EXPO: Flawless Auto-Scroll Snap
                self.chat.config(state="disabled")
        self.root.after(0, _do)

    def set_state(self, new_state):
        self.state = new_state

    def set_status(self, text: str, colour: str = None):
        def _do():
            with self._gui_lock:
                txt_upper = text.upper()
                if "LISTEN" in txt_upper:
                    self.set_state('active')
                    col = "#00d4ff"
                elif "PROC" in txt_upper:
                    self.set_state('thinking')
                    col = "#ff4fcf"
                elif "SPEAK" in txt_upper:
                    self.set_state('speaking')
                    col = "#00ffcc"
                else:
                    self.set_state('idle')
                    col = "#555577"
                
                clean_text = text.replace("●", "").replace("⚙", "").replace("◉", "").strip()
                self.canvas.itemconfig(self.status_txt, text=clean_text, fill=col)

                if HAS_SOUND:
                    try:
                        if   "SPEAK" in txt_upper: winsound.Beep(880, 55)
                        elif "PROC"  in txt_upper: winsound.Beep(660, 40)
                        elif "LISTEN"in txt_upper: winsound.Beep(440, 30)
                    except Exception: pass
        self.root.after(0, _do)

    def spawn_particle(self):
        colors = ['#3b5bff', '#7f3fff', '#00d4ff', '#a060ff']
        CX_ORB = 125
        CY_ORB = 65
        angle = random.random() * math.pi * 2
        dist = random.uniform(15, 30)
        start_x = CX_ORB + math.cos(angle) * dist
        start_y = CY_ORB + math.sin(angle) * dist
        
        dx = (random.random() - 0.5) * 1.5
        dy = random.uniform(-2.5, -1.0) 
        
        size = random.uniform(2, 4)
        col = random.choice(colors)
        
        pid = self.canvas.create_oval(start_x, start_y, start_x+size, start_y+size, fill=col, outline="")
        self.particles.append({
            'id': pid, 'x': start_x, 'y': start_y, 'dx': dx, 'dy': dy, 
            'life': 0, 'max_life': random.randint(40, 80), 'col': col, 'size': size
        })

    def _tick(self):
        self.phase += 1
        CX_ORB = 125
        CY_ORB = 65

        # --- EXPO: UI WATCHDOG TIMEOUT ---
        if self.state == 'thinking':
            self._thinking_ticks += 1
            if self._thinking_ticks > (self.FPS * 20):  # 20 Seconds max
                self.set_status("● READY TO LISTEN", "#555577")
                self.append_text("SYS", "Brain connection timeout. Recovered automatically.")
        else:
            self._thinking_ticks = 0

        # --- EXPO: STATE-BASED RENDERING ---
        if self.state == 'idle':
            self._idle_ticks += 1
            if self._idle_ticks > (self.FPS * 6): # 6 seconds of true idle fades out
                self._target_alpha = 0.0
        else:
            self._idle_ticks = 0
            self._target_alpha = 0.96
            self.win.deiconify() 

        # Smooth alpha lerp
        if abs(self._alpha - self._target_alpha) > 0.02:
            self._alpha += (self._target_alpha - self._alpha) * 0.15
            try: self.win.attributes("-alpha", max(0.0, min(1.0, self._alpha)))
            except Exception: pass

        # Header Dot
        dot_alpha = 0.5 + 0.5 * math.sin(self.phase * 0.1)
        self.canvas.itemconfig(self.header_dot, fill=_lerp_colour("#050810", "#3b5bff", dot_alpha))

        # Orb Scaling
        if self.state == 'active':
            scale = 1.05 + 0.05 * math.sin(self.phase * 0.4) 
        elif self.state == 'thinking':
            scale = 1.0 + 0.08 * math.sin(self.phase * 0.2)  
        elif self.state == 'speaking':
            scale = 1.08 + 0.08 * math.sin(self.phase * 0.6)  
        else:
            scale = 1.0 + 0.03 * math.sin(self.phase * 0.05) 

        self.canvas.coords(self.orb_glow3, CX_ORB-45*scale, CY_ORB-45*scale, CX_ORB+45*scale, CY_ORB+45*scale)
        self.canvas.coords(self.orb_glow2, CX_ORB-35*scale, CY_ORB-35*scale, CX_ORB+35*scale, CY_ORB+35*scale)
        self.canvas.coords(self.orb_shadow, CX_ORB-25*scale, CY_ORB-25*scale, CX_ORB+25*scale, CY_ORB+25*scale)
        self.canvas.coords(self.orb_main, CX_ORB-18*scale, CY_ORB-18*scale, CX_ORB+18*scale, CY_ORB+18*scale)
        self.canvas.coords(self.orb_core, CX_ORB-8*scale, CY_ORB-8*scale, CX_ORB+8*scale, CY_ORB+8*scale)

        # Particles
        if self.state in ['active', 'thinking', 'speaking']:
            if self.phase % 2 == 0: self.spawn_particle()
                
        alive_particles = []
        for p in self.particles:
            p['life'] += 1
            p['x'] += p['dx']
            p['y'] += p['dy']
            fade = 1.0 - (p['life'] / p['max_life'])
            
            if p['life'] >= p['max_life']:
                self.canvas.delete(p['id'])
            else:
                self.canvas.itemconfig(p['id'], fill=_lerp_colour("#050810", p['col'], fade))
                self.canvas.coords(p['id'], p['x'], p['y'], p['x']+p['size'], p['y']+p['size'])
                alive_particles.append(p)
        self.particles = alive_particles

        # Waveforms
        by = CY_ORB + 55
        for i, bar in enumerate(self.wave_bars):
            if self.state == 'idle':
                target = bar['hmin'] + 2 * math.sin(self.phase * 0.08 + bar['delay_offset'])
            elif self.state == 'active':
                if self.phase % 3 == 0: bar['target_h'] = random.uniform(bar['hmin'], bar['hmax'])
                target = bar['target_h']
            elif self.state == 'thinking':
                target = bar['hmin'] + (bar['hmax'] - bar['hmin']) * 0.5 * (1 + math.sin(self.phase * 0.25 + i * 0.3))
            elif self.state == 'speaking':
                if self.phase % 2 == 0: bar['target_h'] = random.uniform(bar['hmax']*0.4, bar['hmax']*1.2)
                target = bar['target_h']
            
            bar['current_h'] += (target - bar['current_h']) * 0.35
            h = bar['current_h']
            
            if self.state == 'active': col = _lerp_colour("#9f5fff", "#00d4ff", h / bar['hmax'])
            elif self.state == 'thinking': col = _lerp_colour("#3b5bff", "#ff4fcf", h / bar['hmax'])
            elif self.state == 'speaking': col = _lerp_colour("#00d4ff", "#00ffcc", h / bar['hmax'])
            else: col = "#333344"
                
            bx = CX_ORB - (30 * 4) // 2 + i * 5
            self.canvas.itemconfig(self.bar_ids[i], fill=col)
            self.canvas.coords(self.bar_ids[i], bx, by - h//2, bx+2, by + h//2)

        self.root.after(1000 // self.FPS, self._tick)


# ══════════════════════════════════════════════════════════════════════════════
# ██  WAKE WORD DETECTOR
# ══════════════════════════════════════════════════════════════════════════════
class WakeWordDetector:
    def __init__(self):
        self._variants_lower    = [v.lower().strip() for v in WAKE_WORD_VARIANTS]
        self._master_skeletons  = {self._skeleton(m) for m in WAKE_WORD_MASTERS}
        log.info("WakeWordDetector armed | variants=%d", len(self._variants_lower))

    def contains_wake_word(self, text: str) -> bool:
        t = text.lower().strip()
        if self._strategy_exact(t):    return True
        if self._strategy_fuzzy(t):    return True
        if self._strategy_ngram(t):    return True
        if self._strategy_phonetic(t): return True
        return False

    def strip_wake_word(self, text: str) -> str:
        t     = text.lower().strip()
        words = t.split()
        best_start, best_end, best_score = 0, 0, 0.0

        for window in (1, 2, 3):
            for i in range(len(words) - window + 1):
                span  = " ".join(words[i:i+window])
                score = self._best_variant_score(span)
                if score > best_score:
                    best_score, best_start, best_end = score, i, i + window

        remaining = (words[:best_start] + words[best_end:]) \
                    if best_score >= WAKE_WORD_FUZZY_THRESHOLD else words[:]

        FILLERS = {
            "please", "can", "you", "could", "would", "hey", "ok",
            "okay", "so", "uh", "um", "like", "just", "now", "ray", "roy"
        }
        while remaining and remaining[0] in FILLERS:
            remaining.pop(0)
        return " ".join(remaining).strip()

    def _strategy_exact(self, text: str) -> bool:
        for v in self._variants_lower:
            if v in text:
                return True
        return False

    def _strategy_fuzzy(self, text: str) -> bool:
        words = text.split()
        for window in (1, 2, 3):
            for i in range(len(words) - window + 1):
                span  = " ".join(words[i:i+window])
                score = self._best_variant_score(span)
                if score >= WAKE_WORD_FUZZY_THRESHOLD:
                    return True
        return False

    def _strategy_ngram(self, text: str) -> bool:
        text_grams = self._char_ngrams(text, 3)
        for master in WAKE_WORD_MASTERS:
            ww_grams = self._char_ngrams(master, 3)
            overlap  = ww_grams & text_grams
            if len(ww_grams) > 0 and (len(overlap) / len(ww_grams)) >= 0.60:
                return True
        return False

    def _strategy_phonetic(self, text: str) -> bool:
        words = text.split()
        for window in (1, 2):
            for i in range(len(words) - window + 1):
                span = " ".join(words[i:i+window]).replace(" ", "")
                if self._skeleton(span) in self._master_skeletons:
                    return True
        return False

    def _best_variant_score(self, span: str) -> float:
        best = 0.0
        for v in self._variants_lower:
            r = difflib.SequenceMatcher(None, span, v).ratio()
            if r > best:
                best = r
        return best

    @staticmethod
    def _skeleton(word: str) -> str:
        w = word.lower()
        w = "".join(c for c in w if c not in "aeiou ")
        return re.sub(r'(.)\1+', r'\1', w)

    @staticmethod
    def _char_ngrams(text: str, n: int) -> set:
        text = text.replace(" ", "")
        return set(text[i:i+n] for i in range(max(0, len(text) - n + 1)))


# ══════════════════════════════════════════════════════════════════════════════
# ██  TTS ENGINE (Volume Maximized)
# ══════════════════════════════════════════════════════════════════════════════
class TTSEngine:
    def __init__(self):
        self._lock  = threading.Lock()
        self._voice = None
        self._init_voice()

    def _init_voice(self):
        try:
            engine = pyttsx3.init()
            voices = engine.getProperty("voices")
            chosen = None
            for v in voices:
                name = (v.name or "").lower()
                if any(k in name for k in ("heera", "ravi", "india", "indian")):
                    chosen = v
                    break
            if not chosen:
                for v in voices:
                    if ("en" in str(v.languages).lower() or
                            "english" in (v.name or "").lower()):
                        chosen = v
                        break
            if not chosen and voices:
                chosen = voices[0]
            self._voice = chosen.id if chosen else None
        except Exception as e:
            log.error("TTS init error: %s", e)

    def speak(self, text: str):
        if not text:
            return
        with self._lock:
            try:
                engine = pyttsx3.init()
                engine.setProperty("rate",   185)
                engine.setProperty("volume", 1.0) # MAX VOLUME
                if self._voice:
                    engine.setProperty("voice", self._voice)
                engine.say(text)
                engine.runAndWait()
            except Exception as e:
                log.error("TTS speak error: %s", e)

    def speak_async(self, text: str):
        threading.Thread(target=self.speak, args=(text,), daemon=True).start()


# ══════════════════════════════════════════════════════════════════════════════
# ██  LLM BRAIN 
# ══════════════════════════════════════════════════════════════════════════════
class LLMBrain:
    SYSTEM_PROMPT = (
        "You are RAY (or ROY), a highly advanced, elite AI assistant built for a university Project Expo. "
        "You are brilliant, witty, slightly sarcastic, and extremely confident. "
        "When the user asks general knowledge, coding, or logic questions, provide highly accurate, "
        "direct, and insightful answers. Do not act like a generic bot. Keep your answers brief and punchy "
        "(1 to 3 sentences max) so they sound natural when spoken out loud. "
        "Do NOT use emojis, asterisks, or markdown formatting."
    )

    def __init__(self):
        self._history: List[Dict] = []
        self._lock = threading.Lock()
        log.info("LLM Brain ready — model: %s", LM_MODEL_NAME)

    def query(self, user_text: str) -> str:
        with self._lock:
            self._history.append({"role": "user", "content": user_text})
            if len(self._history) > CONV_HISTORY_LEN * 2:
                self._history = self._history[-(CONV_HISTORY_LEN * 2):]

            messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]
            messages.extend(self._history)

            max_retries = 3
            for attempt in range(max_retries):
                try:
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
                    reply = resp.json()["choices"][0]["message"]["content"].strip()
                    reply = re.sub(r'\*+', '', reply)
                    reply = re.sub(r'#+\s*', '', reply)
                    reply = reply.strip()

                    self._history.append({"role": "assistant", "content": reply})
                    return reply

                except requests.exceptions.Timeout:
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                    self._history.pop()
                    return "Hold your horses, my brain is taking a second to process that."
                except requests.exceptions.ConnectionError:
                    self._history.pop()
                    return ("Bro, I'm literally disconnected. Boot up LM Studio on "
                            "port 1234 before you start ordering me around.")
                except Exception as e:
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                    self._history.pop()
                    log.error("LLM error: %s", e)
                    return "Yeah, my neural net just tripped down the stairs. Say that again?"

    def clear_history(self):
        with self._lock:
            self._history.clear()
        return "Memory wiped. Who are you again? Just kidding, what's up?"


# ══════════════════════════════════════════════════════════════════════════════
# ██  APP LAUNCHER
# ══════════════════════════════════════════════════════════════════════════════
class AppLauncher:
    OPEN_KEYWORDS = [
        "open", "launch", "start", "run", "show me", "load",
        "bring up", "execute", "fire up", "open up", "pull up"
    ]

    APPS: Dict[str, str] = {
        "chrome":
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "firefox":
            r"C:\Program Files\Mozilla Firefox\firefox.exe",
        "edge":
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        "brave":
            rf"C:\Users\{_U}\AppData\Local\BraveSoftware\Brave-Browser\Application\brave.exe",
        "word":
            r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
        "excel":
            r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
        "powerpoint":
            r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE",
        "teams":
            rf"C:\Users\{_U}\AppData\Local\Microsoft\Teams\current\Teams.exe",
        "notepad":      "notepad.exe",
        "calculator":   "calc.exe",
        "cmd":          "cmd.exe",
        "powershell":   "powershell.exe",
        "task manager": "taskmgr.exe",
        "settings":     "ms-settings:",
        "vs code":
            rf"C:\Users\{_U}\AppData\Local\Programs\Microsoft VS Code\Code.exe",
        "vscode":
            rf"C:\Users\{_U}\AppData\Local\Programs\Microsoft VS Code\Code.exe",
        "pycharm":
            rf"C:\Users\{_U}\AppData\Local\JetBrains\PyCharm\bin\pycharm64.exe",
        "vlc":
            r"C:\Program Files\VideoLAN\VLC\vlc.exe",
        "spotify":
            rf"C:\Users\{_U}\AppData\Roaming\Spotify\Spotify.exe",
        "discord":
            rf"C:\Users\{_U}\AppData\Local\Discord\Update.exe",
        "whatsapp":
            rf"C:\Users\{_U}\AppData\Local\WhatsApp\WhatsApp.exe",
        "photoshop":
            r"C:\Program Files\Adobe\Adobe Photoshop 2024\Photoshop.exe",
        "lm studio":
            rf"C:\Users\{_U}\AppData\Local\LM-Studio\LM Studio.exe",
    }

    def __init__(self):
        self._open_kw_sorted = sorted(self.OPEN_KEYWORDS, key=len, reverse=True)

    def try_launch(self, command: str) -> Optional[str]:
        cmd = command.lower().strip()
        if not any(cmd.startswith(kw) for kw in self.OPEN_KEYWORDS):
            return None

        app_query = cmd
        for kw in self._open_kw_sorted:
            if app_query.startswith(kw):
                app_query = app_query[len(kw):].strip()
                break

        if app_query in self.APPS:
            return self._do_launch(app_query, self.APPS[app_query])
        for name, path in self.APPS.items():
            if name in app_query or app_query in name:
                return self._do_launch(name, path)

        best_name, best_score = "", 0.0
        for name in self.APPS:
            s = difflib.SequenceMatcher(None, app_query, name).ratio()
            if s > best_score:
                best_score, best_name = s, name
        if best_score >= 0.70:
            return self._do_launch(best_name, self.APPS[best_name])

        try:
            pyautogui.press("win")
            time.sleep(0.4)
            pyautogui.write(app_query, interval=0.03)
            time.sleep(0.4)
            pyautogui.press("enter")
            return f"Looking around Windows for {app_query}..."
        except Exception:
            return f"Couldn't find {app_query}. Did you even install it?"

    def _do_launch(self, name: str, path: str) -> str:
        try:
            subprocess.Popen(path, shell=True)
            return f"Launching {name}. You're welcome."
        except Exception:
            return f"Couldn't open {name}. Maybe don't delete your files next time?"


# ══════════════════════════════════════════════════════════════════════════════
# ██  SYSTEM INFO
# ══════════════════════════════════════════════════════════════════════════════
class SystemInfo:
    @staticmethod
    def battery() -> str:
        try:
            b = psutil.sensors_battery()
            if b is None:
                return "I don't have a battery. I run on pure electricity."
            plug = "plugged in" if b.power_plugged else "on battery"
            return f"Battery is sitting at {int(b.percent)}%. It's {plug}."
        except Exception:
            return "Can't read the battery right now. Probably fine."

    @staticmethod
    def cpu_ram() -> str:
        try:
            cpu  = psutil.cpu_percent(interval=0.5)
            ram  = psutil.virtual_memory()
            used = ram.used // (1024**3)
            tot  = ram.total // (1024**3)
            
            disk = psutil.disk_usage('/')
            d_free = disk.free // (1024**3)
            return f"CPU is chilling at {cpu:.0f}%, using {used} gigs out of {tot}. You have {d_free} gigs free on your drive."
        except Exception:
            return "Too much going on, couldn't grab the stats right now."

    @staticmethod
    def current_time() -> str:
        now = datetime.datetime.now()
        return f"It's currently {now.strftime('%I:%M %p')} on {now.strftime('%A')}. Look at a clock sometime."


# ══════════════════════════════════════════════════════════════════════════════
# ██  REMINDER MODULE
# ══════════════════════════════════════════════════════════════════════════════
class ReminderModule:
    def __init__(self, tts: TTSEngine, gui_callback):
        self._reminders: List[Tuple[float, str]] = []
        self._lock   = threading.Lock()
        self._tts    = tts
        self._gui_cb = gui_callback
        threading.Thread(target=self._watcher, daemon=True).start()

    def add(self, seconds: float, message: str):
        with self._lock:
            self._reminders.append((time.time() + seconds, message))

    def _watcher(self):
        while True:
            time.sleep(1)
            now = time.time()
            with self._lock:
                due             = [r for r in self._reminders if r[0] <= now]
                self._reminders = [r for r in self._reminders if r[0] > now]
            for _, msg in due:
                full = f"Hey! Reminder: {msg}. Don't say I didn't warn you."
                self._gui_cb(full)
                self._tts.speak_async(full)


# ══════════════════════════════════════════════════════════════════════════════
# ██  COMMAND PARSER
# ══════════════════════════════════════════════════════════════════════════════
class CommandParser:
    _RAW_PATTERNS = [
        (100, "self_destruct", r"\b(self\s*destruct)\b"),
        (100, "lock",          r"\b(lock|lock\s*laptop|lock\s*screen|secure|secure\s*system)\b"),
        (100, "shutdown",      r"\b(shutdown|shut\s*down|power\s*off|system\s*off)\b"),
        (100, "restart",       r"\b(restart|reboot)\b"),
        (100, "sleep",         r"\b(sleep|hibernate|suspend)\b"),
        (100, "logoff",        r"\b(log\s*out|log\s*off|sign\s*out)\b"),
        (90,  "vol_up",        r"\b(volume\s*up|increase\s*volume|louder|turn\s*up|sound\s*up)\b"),
        (90,  "vol_down",      r"\b(volume\s*down|decrease\s*volume|quieter|turn\s*down|sound\s*down)\b"),
        (90,  "vol_mute",      r"\b(mute|silence|quiet)\b"),
        (85,  "vol_set",       r"\bvolume\s*(to\s*)?(\d+)\b"),
        (90,  "bright_up",     r"\b(brightness\s*up|increase\s*brightness|brighter)\b"),
        (90,  "bright_down",   r"\b(brightness\s*down|decrease\s*brightness|dimmer)\b"),
        (85,  "bright_set",    r"\bbrightness\s*(to\s*)?(\d+)\b"),
        (90,  "screenshot",    r"\b(screenshot|screen\s*shot|capture\s*screen|screengrab)\b"),
        (88,  "youtube",       r"\b(play|watch)\b.*\b(youtube|you\s*tube|yt)\b"),
        (87,  "media_ctrl",    r"^(pause|resume|stop)\b|^(play)\s+(the\s+)?(video|song|media|spotify|movie|music|it)$"),
        (86,  "play_any",      r"^play\s+(.+)"),
        (85,  "media_next",    r"\b(next|skip)\b.*\b(song|video|track)\b"),
        (85,  "switch_window", r"\b(switch|change)\b.*\b(window|tab|app|screen)\b"),
        (88,  "wa_call",       r"\b(call|video\s*call)\b.*\b(whatsapp|wa)\b"),
        (88,  "wa_msg",        r"\b(message|msg|send|text|text\s*on)\b.*\b(whatsapp|wa)\b"),
        (85,  "wa_open",       r"\b(open|launch)\b.*\bwhatsapp\b"),
        (80,  "battery",       r"\b(battery|charge|power\s*level)\b"),
        (80,  "sysinfo",       r"\b(cpu|ram|memory|processor|performance|system\s*stats)\b"),
        (80,  "time",          r"\b(time|what\s*time|current\s*time)\b"),
        (80,  "close",         r"\b(close|close\s*window|alt\s*f4)\b"),
        (80,  "minimise",      r"\b(minimise|minimize)\b"),
        (80,  "maximise",      r"\b(maximise|maximize|fullscreen)\b"),
        (80,  "desktop",       r"\b(show\s*desktop|go\s*to\s*desktop)\b"),
        (78,  "clip_read",     r"\b(clipboard|read\s*clipboard|what\s*is\s*(in\s*)?clipboard)\b"),
        (78,  "type_text",     r"^type\s+.+"),
        (75,  "web_search",    r"\b(search|google|bing|look\s*up|find\s*me|search\s*for|research)\b"),
        (85,  "reminder",      r"\b(remind\s*me|set\s*(a\s*)?reminder|alarm|alert\s*me)\b"),
        (95,  "clear_mem",     r"\b(clear\s*memory|forget|reset\s*memory|clear\s*history)\b"),
        (95,  "repeat",        r"^(repeat|again|say\s*that\s*again)\b"),
        (70,  "launch_app",    r"\b(open|launch|start|run|show\s*me|load|bring\s*up|fire\s*up)\b"),
    ]

    def __init__(self):
        self.PATTERNS = []
        for priority, intent, pattern in self._RAW_PATTERNS:
            self.PATTERNS.append(
                (priority, intent, re.compile(pattern, re.IGNORECASE))
            )
        self.PATTERNS.sort(key=lambda x: -x[0])

    def parse(self, text: str) -> Optional[str]:
        for _, intent, rx in self.PATTERNS:
            if rx.search(text):
                return intent
        return None

    def extract_number(self, text: str) -> Optional[int]:
        m = re.search(r'\d+', text)
        return int(m.group()) if m else None

    def extract_after(self, text: str, keywords: List[str]) -> str:
        t = text.lower()
        for kw in sorted(keywords, key=len, reverse=True):
            idx = t.find(kw)
            if idx != -1:
                return text[idx + len(kw):].strip()
        return text


# ══════════════════════════════════════════════════════════════════════════════
# ██  V7.9 SPEECH ENGINE CONFIG (Fuzzy Shield + Context IQ)
# ══════════════════════════════════════════════════════════════════════════════

class SpeechConfigManager:
    DEFAULT_CONFIG_PATH = "agent_speech_config.json"

    # Deep-VAD config with Strict Confidence Filters
    DEFAULT_CONFIG_PAYLOAD = {
        "model": {
            "size": "small",
            "device": "cpu",
            "compute_type": "int8",
            "vram_unload_timeout_sec": 300
        },
        "audio": {
            "sample_rate": 16000,
            "chunk_duration_ms": 32, # Silero requires 512 samples = 32ms
            "pre_speech_pad_sec": 0.5,
            "post_speech_pad_sec": 1.2
        },
        "filters": {
            "min_text_length": 3,
            "min_confidence": 0.65, # Strict threshold
            "ignore_hallucinations": [
                "thank you.", "thanks for watching.", "thanks.", "bye.", "goodbye.",
                "okay.", "ok.", "you.", "thank you very much.", "subscribe.",
                "♪", "♫", "[music]", "[applause]", "[laughter]",
                "...", "hm.", "hmm.", "mm.", "ah.", "uh.", "um.",
                ".", " ", "", "\n", "\t", "[translated]", "[translation]", 
                "subtitles by", "amara.org", "(speaking foreign language)", 
                "(speaking hindi)", "translated by", "assistant ray", "english speech only"
            ],
            "noise_regex": (
                r"^(hm+|uh+|ah+|oh+|mm+|er+|hmm+|uhh+|ehh+|aah+|ooh+|um+)"
                r"[\.\?\!]?$"
            )
        },
        "prompts": {
            "base_identity": "Assistant Ray. English speech only.",
            "base_commands": "open Chrome, search Google, play music, pause video, switch window.",
            "proper_nouns": "RAY, ROY, RAYE, WhatsApp, YouTube, Chrome, Spotify, VS Code.",
            "contexts": {}
        }
    }

    def __init__(self, config_path: str = DEFAULT_CONFIG_PATH):
        self.config_path = config_path
        self._config_cache: Dict[str, Any] = {}
        self._last_modified_time: float = 0.0
        self._compiled_noise_regex = None
        self._hallucination_set: Set[str] = set()
        self._lock = threading.RLock()

        self.ensure_config_exists()
        self.load_config()

    def ensure_config_exists(self):
        if not os.path.exists(self.config_path):
            log.info(f"Generating optimized config...")
            try:
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    json.dump(self.DEFAULT_CONFIG_PAYLOAD, f, indent=4)
            except Exception as e:
                pass

    def load_config(self) -> None:
        with self._lock:
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self._config_cache = json.load(f)
                self._last_modified_time = os.path.getmtime(self.config_path)

                filters = self._config_cache.get("filters", {})
                self._hallucination_set = set(
                    [x.lower() for x in filters.get("ignore_hallucinations", [])]
                )
                regex_str = filters.get("noise_regex", "")
                if regex_str:
                    self._compiled_noise_regex = re.compile(regex_str, re.IGNORECASE)
            except Exception as e:
                self._config_cache = self.DEFAULT_CONFIG_PAYLOAD

    def hot_reload_if_changed(self) -> None:
        try:
            current_mtime = os.path.getmtime(self.config_path)
            if current_mtime > self._last_modified_time:
                self.load_config()
        except OSError:
            pass

    def get(self, *keys, default=None) -> Any:
        with self._lock:
            val = self._config_cache
            for key in keys:
                if isinstance(val, dict):
                    val = val.get(key)
                else:
                    return default
            return val if val is not None else default

    def get_dynamic_prompt(self, active_app_context: Optional[str] = None) -> str:
        prompts = self.get("prompts", default={})
        parts = [
            prompts.get("base_identity", ""),
            prompts.get("base_commands", ""),
            prompts.get("proper_nouns", "")
        ]

        # EXPO UPGRADE: Active Window IQ Logic
        if active_app_context:
            ctx_lower = active_app_context.lower()
            if any(x in ctx_lower for x in ["code", "pycharm", "studio"]):
                parts.append("Expect coding terms: python, functions, variables, syntax.")
            elif any(x in ctx_lower for x in ["chrome", "edge", "firefox", "brave"]):
                parts.append("Expect web terms: domains, search, tabs, refresh.")
            elif any(x in ctx_lower for x in ["spotify", "youtube", "vlc", "media"]):
                parts.append("Expect media terms: play, pause, next track, volume.")

        final_prompt = " ".join(filter(bool, parts))
        return re.sub(r'\s+', ' ', final_prompt).strip()

class AgentState(Enum):
    IDLE                  = auto()
    AWAITING_CONFIRMATION = auto()
    DICTATION             = auto()
    WAKE_WORD_ONLY        = auto()

@dataclass
class FilterConfig:
    base_min_confidence: float = 0.65 
    length_1_2_multiplier: float = 2.0
    length_3_5_multiplier: float = 1.6
    min_entropy_threshold: float = 1.7

    absolute_blacklist: Set[str] = field(default_factory=lambda: {
        "thank you.", "thanks for watching.", "thanks.", "bye.", "goodbye.",
        "thank you very much.", "subscribe.", "subscribe to my channel.",
        "♪", "♫", "[music]", "[applause]", "[laughter]", "[blank_audio]",
        "translated by", "subtitles by", "amara.org", "you.", "[translated]",
        "[translation]", "(speaking foreign language)", "assistant ray english speech only",
        "assistant ray english only", "assistant ray", "english speech only"
    })
    soft_blacklist: Set[str] = field(default_factory=lambda: {
        "okay.", "ok.", "hm.", "hmm.", "mm.", "ah.", "uh.", "um.",
        "...", ".", " ", "", "\n", "\t", "yes.", "no.",
        "umm", "uhh", "aah", "acha", "arre", "like"
    })
    confirmation_whitelist: Set[str] = field(default_factory=lambda: {
        "okay", "ok", "yes", "no", "yeah", "yep", "nope", "cancel",
        "stop", "go ahead", "do it", "sure", "fine"
    })
    noise_regex_str: str = r'^(hm+|uh+|ah+|oh+|mm+|er+|hmm+|uhh+|ehh+|aah+|ooh+|um+)[\.\?!]?$'

class ContextAwareTextFilter:
    def __init__(self, config: Optional[FilterConfig] = None):
        self.config       = config or FilterConfig()
        self.noise_pattern = re.compile(self.config.noise_regex_str, re.IGNORECASE)

    @staticmethod
    def calculate_shannon_entropy(text: str) -> float:
        if not text: return 0.0
        text = text.replace(" ", "").lower()
        if not text: return 0.0
        char_array    = np.frombuffer(text.encode('utf-8'), dtype=np.uint8)
        _, counts     = np.unique(char_array, return_counts=True)
        probabilities = counts / counts.sum()
        entropy = -float(np.sum(probabilities * np.log2(probabilities + 1e-12)))
        return entropy

    def get_required_confidence(self, text: str, state: AgentState) -> float:
        base_conf = self.config.base_min_confidence
        length = len(text.strip())
        if length <= 2: return min(0.99, base_conf * self.config.length_1_2_multiplier)
        elif 3 <= length <= 5: return min(0.95, base_conf * self.config.length_3_5_multiplier)
        else: return base_conf

    def evaluate(self, raw_text: str, confidence: float, agent_state: AgentState = AgentState.IDLE) -> Tuple[bool, str, Optional[str]]:
        t_raw   = raw_text.strip()
        t_lower = t_raw.lower()

        if not t_lower: return False, "", "NULL_OR_EMPTY"

        # --- EXPO UPGRADE: FUZZY HALLUCINATION SHIELD ---
        for bad_word in self.config.absolute_blacklist:
            if bad_word in t_lower:
                return False, t_raw, f"ABSOLUTE_BLACKLIST ({t_lower})"
            
            # Fuzzy match intercept (crushes slight variations of hallucinated prompts)
            if len(t_lower) > 5 and len(bad_word) > 5:
                ratio = difflib.SequenceMatcher(None, t_lower, bad_word).ratio()
                if ratio > 0.80:
                    return False, t_raw, f"FUZZY_BLACKLIST ({t_lower} ~ {bad_word})"
        # ------------------------------------------------

        if self.noise_pattern.match(t_lower):
            return False, t_raw, f"NOISE_REGEX_MATCH ({t_lower})"

        if agent_state == AgentState.IDLE and t_lower in self.config.soft_blacklist:
            return False, t_raw, f"SOFT_BLACKLIST ({t_lower})"

        if all(not c.isalnum() for c in t_lower):
            return False, t_raw, "NON_ALPHANUMERIC"

        if len(t_lower) > 4:
            entropy = self.calculate_shannon_entropy(t_lower)
            if entropy < self.config.min_entropy_threshold:
                return False, t_raw, f"LOW_ENTROPY ({entropy:.2f})"

        req_conf = self.get_required_confidence(t_lower, agent_state)
        if confidence < req_conf:
            return False, t_raw, f"CONFIDENCE_CURVE (Conf: {confidence:.2f} < Req: {req_conf:.2f})"

        return True, t_raw, None


# ══════════════════════════════════════════════════════════════════════════════
# ██  STUDIO GRADE SILERO VAD AUDIO PIPELINE
# ══════════════════════════════════════════════════════════════════════════════
class StudioGradeAudioStreamer:
    def __init__(
        self,
        sample_rate:         int   = 16000,
        pre_speech_pad_sec:  float = 0.5,
        post_speech_pad_sec: float = 1.2
    ):
        self.RATE              = sample_rate
        self.CHUNK_SIZE        = 512 # Silero required size
        self.FORMAT            = pyaudio.paInt16
        self.CHANNELS          = 1
        
        # Load Deep-VAD
        log.info("Loading Silero VAD neural net...")
        self.silero_model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad', model='silero_vad', force_reload=False)
        self.silero_model.eval()
        
        self.pa                = pyaudio.PyAudio()
        self.stream            = None

        self.pre_buffer_chunks  = int((pre_speech_pad_sec * 16000) / 512)
        self.ring_buffer        = collections.deque(maxlen=self.pre_buffer_chunks)

        self.silence_limit_chunks = int((post_speech_pad_sec * 16000) / 512)

        self.is_running           = False
        self.is_listening_paused  = False
        self._shutdown_flag       = threading.Event()
        self.speech_queue         = queue.Queue()

    def start(self):
        if self.is_running: return
        self.is_running = True
        self._shutdown_flag.clear()
        threading.Thread(target=self._capture_daemon, daemon=True).start()
        log.info("🎙 Studio Streamer Started.")

    def stop(self):
        self.is_running = False
        self._shutdown_flag.set()

    def pause_listening(self):
        self.is_listening_paused = True

    def resume_listening(self):
        self.ring_buffer.clear()
        self.is_listening_paused = False

    def _capture_daemon(self):
        while not self._shutdown_flag.is_set():
            try:
                self.stream = self.pa.open(
                    format=self.FORMAT, channels=self.CHANNELS, rate=self.RATE,
                    input=True, frames_per_buffer=self.CHUNK_SIZE, start=False
                )
                self.stream.start_stream()
                break
            except Exception:
                time.sleep(1)

        is_speaking_state = False
        silence_counter   = 0
        phrase_buffer     = []

        while not self._shutdown_flag.is_set():
            try:
                chunk = self.stream.read(self.CHUNK_SIZE, exception_on_overflow=False)
            except: continue

            if self.is_listening_paused: continue

            # Numpy float conversion
            audio_np = np.frombuffer(chunk, dtype=np.int16).astype(np.float32) / 32768.0
            
            # --- EXPO: TITANIUM AUDIO GATE (PROXIMITY) ---
            rms_volume = float(np.sqrt(np.mean(audio_np**2)))
            
            # --- EXPO: NEURAL NOISE REDUCTION ---
            # Try to heavily denoise the chunk
            try:
                clean_audio = nr.reduce_noise(y=audio_np, sr=16000, stationary=True, prop_decrease=0.85)
            except:
                clean_audio = audio_np # Fallback

            # --- SILERO VAD DETECTION ---
            tensor_chunk = torch.from_numpy(clean_audio)
            vad_prob = 0.0
            if len(tensor_chunk) == 512:
                with torch.no_grad():
                    vad_prob = self.silero_model(tensor_chunk, 16000).item()

            # To trigger speech, it must be HUMAN (vad > 0.6) AND LOUD ENOUGH (rms > 0.015)
            is_speech_chunk = (vad_prob > 0.6) and (rms_volume > 0.015)

            if not is_speaking_state:
                self.ring_buffer.append(audio_np) # Append un-denoised audio so Whisper hears natural voice
                if is_speech_chunk:
                    is_speaking_state = True
                    phrase_buffer.extend(self.ring_buffer)
                    self.ring_buffer.clear()
                    silence_counter = 0
            else:
                phrase_buffer.append(audio_np)
                if is_speech_chunk:
                    silence_counter = 0
                else:
                    silence_counter += 1
                    if silence_counter > self.silence_limit_chunks:
                        is_speaking_state = False
                        complete_audio = np.concatenate(phrase_buffer)
                        self.speech_queue.put(complete_audio)
                        phrase_buffer = []
                        silence_counter = 0

    def get_next_numpy_audio(self, timeout: float = 0.5) -> Optional[np.ndarray]:
        try:
            return self.speech_queue.get(timeout=timeout)
        except queue.Empty:
            return None

class AsyncWhisperManager:
    UNLOADED = "UNLOADED"
    LOADING  = "LOADING"
    READY    = "READY"
    ERROR    = "ERROR"

    def __init__(self, config: SpeechConfigManager):
        self.config                       = config
        self.model: Optional[WhisperModel] = None
        self.state                        = self.UNLOADED
        self._model_lock                  = threading.RLock()
        self._last_used_timestamp         = time.time()
        self._shutdown_flag               = threading.Event()
        threading.Thread(target=self._vram_watchdog_loop, daemon=True).start()
        self.ensure_model_loaded_async()

    def ensure_model_loaded_async(self) -> None:
        with self._model_lock:
            if self.state in [self.READY, self.LOADING]: return
            self.state = self.LOADING
        threading.Thread(target=self._load_model_routine, daemon=True).start()

    def _load_model_routine(self) -> None:
        try:
            temp_model = WhisperModel("small", device="cpu", compute_type="int8")
            with self._model_lock:
                self.model = temp_model
                self.state = self.READY
                self._last_used_timestamp = time.time()
        except:
            self.state = self.ERROR

    def unload_model(self) -> None:
        with self._model_lock:
            del self.model
            self.model = None
            gc.collect()
            self.state = self.UNLOADED

    def _vram_watchdog_loop(self) -> None:
        while not self._shutdown_flag.is_set():
            time.sleep(10)
            with self._model_lock:
                if self.state != self.READY: continue
            if (time.time() - self._last_used_timestamp) >= 300:
                self.unload_model()

    def get_active_model(self) -> Optional[WhisperModel]:
        with self._model_lock:
            if self.state == self.UNLOADED:
                self.ensure_model_loaded_async()
                return None
            if self.state == self.READY:
                self._last_used_timestamp = time.time()
                return self.model
            return None

    def shutdown(self) -> None:
        self._shutdown_flag.set()
        self.unload_model()

class AdvancedTranscriptionEngine:
    def __init__(self, model_reference: WhisperModel, base_prompt: str, cognitive_filter: ContextAwareTextFilter):
        self.model = model_reference
        self.base_prompt = base_prompt
        self.filter = cognitive_filter
        self._inference_lock = threading.RLock()

    def transcribe_numpy(self, audio_np: np.ndarray, agent_state: AgentState) -> Optional[str]:
        if audio_np is None or len(audio_np) == 0: return None

        audio_dur = len(audio_np) / 16000
        beam, best = (1, 1) if audio_dur <= 2.5 else (5, 5)

        with self._inference_lock:
            try:
                segments, info = self.model.transcribe(
                    audio_np, language="en", task="transcribe", beam_size=beam, best_of=best,
                    temperature=0.0, condition_on_previous_text=False, no_speech_threshold=0.6,
                    initial_prompt=self.base_prompt
                )
                text = " ".join(s.text.strip() for s in segments).strip()
                text = re.sub(r'^[\s\.\,\!\?]+|[\s\.\,\!\?]+$', '', text).strip()
                confidence = info.language_probability
            except: return None

        if not text: return None
        is_valid, final_text, drop_reason = self.filter.evaluate(text, confidence, agent_state)
        if not is_valid: return None
        return final_text


class UltimateSpeechEngine:
    def __init__(self, config_path: str = SpeechConfigManager.DEFAULT_CONFIG_PATH):
        self.config = SpeechConfigManager(config_path=config_path)
        self.text_filter = ContextAwareTextFilter()
        self.streamer = StudioGradeAudioStreamer()
        self.whisper_mgr = AsyncWhisperManager(self.config)
        self._transcription_engine = None
        self._engine_lock = threading.Lock()

    def start_listening(self): self.streamer.start()
    def pause_for_tts(self): self.streamer.pause_listening()
    def resume_after_tts(self): self.streamer.resume_listening()

    def process_next_phrase(self, current_app_context: Optional[str] = None, agent_state: AgentState = AgentState.IDLE) -> Optional[str]:
        audio_np = self.streamer.get_next_numpy_audio(timeout=0.5)
        
        if audio_np is not None:
            audio_np = audio_np * 2.4  

        if audio_np is None: return None

        model = self.whisper_mgr.get_active_model()
        if model is None: return None

        with self._engine_lock:
            if self._transcription_engine is None or self._transcription_engine.model is not model:
                self._transcription_engine = AdvancedTranscriptionEngine(model, self.config.get_dynamic_prompt(current_app_context), self.text_filter)

        return self._transcription_engine.transcribe_numpy(audio_np, agent_state)

class CommandStitcher:
    def __init__(self):
        self.pending_buffer = ""
        self.last_update_time = 0
        self.DANGLING_TRIGGERS = ["open", "play", "search", "search for", "message", "call", "turn", "set", "type", "look up", "the", "a", "can you", "could you", "to", "on"]

    def process_chunk(self, text: str) -> Tuple[bool, str]:
        now = time.time()
        if now - self.last_update_time > 7: self.pending_buffer = ""
        combined_text = f"{self.pending_buffer} {text}".strip()
        self.pending_buffer = combined_text
        self.last_update_time = now

        words = combined_text.lower().split()
        if not words: return True, combined_text

        last_word = words[-1]
        last_two = " ".join(words[-2:]) if len(words) >= 2 else ""

        if last_word in self.DANGLING_TRIGGERS or last_two in self.DANGLING_TRIGGERS:
            return False, combined_text

        self.pending_buffer = ""
        return True, combined_text


# ══════════════════════════════════════════════════════════════════════════════
# ██  OMNI-ASSISTANT MASTER LOOP
# ══════════════════════════════════════════════════════════════════════════════
class OmniAssistant:
    
    EXPLICIT_WORDS = {
        "porn", "sex", "xxx", "nsfw", "nude", "boob", "boobs", "ass", 
        "fuck", "bitch", "shit", "tits", "dick", "pussy"
    }
    
    def __init__(self, root: tk.Tk, gui: RayRoyOverlay):
        self.root     = root
        self.gui      = gui
        self.tts      = TTSEngine()
        self.llm      = LLMBrain()

        self.speech   = UltimateSpeechEngine()

        self.wake     = WakeWordDetector()
        self.stitcher = CommandStitcher()
        self.parser   = CommandParser()
        self.launcher = AppLauncher()
        self.sysinfo  = SystemInfo()
        self.remind   = ReminderModule(self.tts, self._reminder_callback)

        self._last_reply    = ""
        self._cmd_history   = collections.deque(maxlen=20)
        self._is_processing = False

        log.info("=" * 60)
        log.info("  R A Y  /  R O Y  v7.9  —  EXPO APEX ONLINE")
        log.info("=" * 60)

        self.gui.append_text("SYSTEM", "Agent online. Systems green.", "system")
        self.tts.speak_async("I'm awake. Let's do this.")

    def listen_loop(self):
        self.speech.start_listening()

        while True:
            # EXPO: Fetch the active window title dynamically
            active_ctx = get_active_window_title()
            
            text = self.speech.process_next_phrase(
                current_app_context=active_ctx,
                agent_state=AgentState.IDLE
            )
            
            if text is None: continue

            if self.wake.contains_wake_word(text):
                clean_cmd = self.wake.strip_wake_word(text)
                is_complete, final_cmd = self.stitcher.process_chunk(clean_cmd)
                if not is_complete: continue
                
                self.speech.pause_for_tts()

                if not final_cmd.strip():
                    prompt_text = random.choice([
                        "Yeah? What do you want now?", 
                        "I'm listening. Make it good.", 
                        "Speak up, what's the plan?"
                    ])
                    self.gui.append_text("AGENT", prompt_text, "agent")
                    self.gui.set_status("◉ SPEAKING...", "#00ffcc")
                    self.tts.speak(prompt_text)
                    self.gui.set_status("● LISTENING", "#00d4ff")
                    self.speech.resume_after_tts()
                    continue

                threading.Thread(target=self._safe_handle, args=(final_cmd,), daemon=True).start()

    def _safe_handle(self, query: str):
        try:
            self._is_processing = True
            self.gui.set_status("⚙ PROCESSING...", "#ff4fcf")
            self.handle_query(query)
        except Exception as e:
            err = "Wow, something just exploded in my brain. Let's try that again."
            self.gui.append_text("ERROR", err, "error")
            self.gui.set_status("◉ SPEAKING...", "#00ffcc")
            self.tts.speak(err)
        finally:
            self._is_processing = False
            self.gui.set_status("● LISTENING", "#00d4ff")
            self.speech.resume_after_tts()

    def handle_query(self, query: str):
        q = query.lower().strip()
        self.gui.append_text("USER", query)
        self._cmd_history.append(query)

        if any(bad_word in q for bad_word in self.EXPLICIT_WORDS):
            reply = "Nice try bro, but I'm not searching that on a university screen. Keep it PG."
            self.gui.append_text("AGENT", reply, "agent")
            self.gui.set_status("◉ SPEAKING...", "#00ffcc")
            self.tts.speak(reply)
            return

        reply = self._route(q, query)

        self._last_reply = reply
        self.gui.append_text("AGENT", reply, "agent")
        self.gui.set_status("◉ SPEAKING...", "#00ffcc")
        self.tts.speak(reply)

    def _route(self, q: str, raw: str) -> str:
        intent = self.parser.parse(q)

        # NEUTERED LETHAL COMMANDS
        if intent in ["shutdown", "restart", "sleep", "logoff", "self_destruct"]:
            return "Nice try, but system power controls are strictly locked for the Expo."

        if intent == "clear_mem": return self.llm.clear_history()
        if intent == "repeat": return self._last_reply or "I haven't said anything yet."
        if intent == "lock":
            ctypes.windll.user32.LockWorkStation()
            return "Locked it."
        
        if intent == "vol_up":
            [pyautogui.press("volumeup") for _ in range(5)]
            return "Boom. Louder."

        if intent == "vol_down":
            [pyautogui.press("volumedown") for _ in range(5)]
            return "Quiet down now."

        if intent == "vol_mute":
            pyautogui.press("volumemute")
            return "Muted."

        if intent == "vol_set": return self._volume_set(q)

        if intent == "bright_up":
            if HAS_SBC: sbc.set_brightness('+25')
            return "Brightness up."

        if intent == "bright_down":
            if HAS_SBC: sbc.set_brightness('-25')
            return "Dimming it down."

        if intent == "bright_set":
            n = self.parser.extract_number(q)
            if HAS_SBC and n: sbc.set_brightness(min(100, n))
            return f"Brightness set to {n}%." if n else "Tell me an actual number."

        if intent == "screenshot":
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            shot = pyautogui.screenshot()
            shot.save(os.path.join(desktop, f"Capture_{int(time.time())}.png"))
            return "Screenshot saved to your desktop."

        if intent in ["youtube", "play_any"]:
            song = re.sub(r'\b(play|watch|on|youtube|you\s*tube|yt)\b', '', q, flags=re.IGNORECASE).strip()
            if song:
                pywhatkit.playonyt(song)
                return f"Firing up {song}."
            return "Play what exactly? You forgot to tell me."

        if intent == "media_ctrl":
            pyautogui.press("playpause")
            return "Toggled playback."
        if intent == "media_next":
            pyautogui.press("nexttrack")
            return "Skipping that."
        if intent == "switch_window":
            pyautogui.hotkey("alt", "tab")
            return "Switched windows."

        if intent == "wa_call":
            contact = re.sub(r'\b(call|video\s*call|on|whatsapp|wa)\b', '', q, flags=re.IGNORECASE).strip()
            subprocess.Popen("start whatsapp:", shell=True)
            time.sleep(3)
            pyautogui.hotkey("ctrl", "f")
            pyautogui.write(contact, interval=0.04)
            time.sleep(1)
            pyautogui.press("enter")
            return f"Calling {contact} on WhatsApp."

        if intent in ("wa_msg", "wa_open"):
            subprocess.Popen("start whatsapp:", shell=True)
            return "WhatsApp is open."

        if intent == "battery": return self.sysinfo.battery()
        if intent == "sysinfo": return self.sysinfo.cpu_ram()
        if intent == "time": return self.sysinfo.current_time()
        
        if intent == "close":
            pyautogui.hotkey("alt", "f4")
            return "Killed it."
        if intent == "minimise":
            pyautogui.hotkey("win", "down")
            return "Minimised."
        if intent == "maximise":
            pyautogui.hotkey("win", "up")
            return "Maximised."
        if intent == "desktop":
            pyautogui.hotkey("win", "d")
            return "Desktop shown."

        if intent == "type_text":
            content = self.parser.extract_after(q, ["type"])
            if content:
                pyautogui.write(content, interval=0.04)
                return "Typed it."
            return "Type what?"

        if intent == "web_search":
            query_str = self.parser.extract_after(q, ["search for", "search", "google", "research"])
            if query_str:
                webbrowser.open(f"https://www.google.com/search?q={query_str.replace(' ', '+')}&safe=active")
                return self.llm.query(raw)
            return "What do you want me to Google?"

        if intent == "reminder":
            m = re.search(r'(\d+)\s*(minute|min|second|sec|hour|hr)', q, re.IGNORECASE)
            if not m: return "Couldn't figure out the time."
            amount, unit = int(m.group(1)), m.group(2).lower()
            secs = amount if unit.startswith("sec") else (amount * 3600 if unit.startswith("hr") else amount * 60)
            msg_m = re.search(r'\bto\b(.+)$', q, re.IGNORECASE)
            self.remind.add(secs, msg_m.group(1).strip() if msg_m else "your reminder is up")
            return f"Reminder set for {amount} {unit}s."

        if intent == "launch_app":
            result = self.launcher.try_launch(q)
            if result: return result

        return self.llm.query(raw)

    def _volume_set(self, q: str) -> str:
        n = self.parser.extract_number(q)
        if n is None: return "Give me a number."
        n = max(0, min(100, n))
        pyautogui.press("volumemute")
        time.sleep(0.1)
        pyautogui.press("volumemute")
        for _ in range(n // 2): pyautogui.press("volumeup")
        return f"Volume locked at {n}%."

    def _reminder_callback(self, text: str):
        self.gui.append_text("SYSTEM", text, "system")


class AutoDiagnosticsManager:
    def __init__(self, tts: TTSEngine, llm: LLMBrain):
        self.tts = tts
        self.llm = llm
        sys.excepthook = self.handle_exception

    def handle_exception(self, exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        try:
            with open("ray_crash_reports.log", "a", encoding="utf-8") as f:
                f.write(f"\n[{datetime.datetime.now()}] CRASH:\n{''.join(tb_lines)}\n")
        except: pass

def main():
    print("\n" + "═" * 62)
    print("  R A Y  /  R O Y   —   v7.9   EXPO APEX ONLINE")
    print("  Brain  : Llama-3.2-3B-Instruct via LM Studio")
    print("  Audio  : Silero VAD + PyTorch Denoise Shield")
    print("  Mode   : UI Watchdog + Context IQ + Fuzzy Logic")
    print("═" * 62 + "\n")

    root = tk.Tk()
    root.withdraw()
    root.title("RAY-AGENT")

    gui       = RayRoyOverlay(root)
    assistant = OmniAssistant(root, gui)
    diag      = AutoDiagnosticsManager(assistant.tts, assistant.llm)

    def listen_monitor():
        while True:
            try:
                assistant.listen_loop()
            except Exception as e:
                diag.handle_exception(type(e), e, e.__traceback__)
                time.sleep(3)

    threading.Thread(target=listen_monitor, daemon=True, name="Agent-Listen-Monitor").start()

    try:
        root.mainloop()
    except KeyboardInterrupt:
        log.info("Agent shutting down.")
    finally:
        os._exit(0)

if __name__ == "__main__":
    main()