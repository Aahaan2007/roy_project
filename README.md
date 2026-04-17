<div align="center">

```
███████╗ ██████╗  ██████╗
██╔════╝██╔════╝ ██╔═══██╗
█████╗  ██║  ███╗██║   ██║
██╔══╝  ██║   ██║██║   ██║
███████╗╚██████╔╝╚██████╔╝
╚══════╝ ╚═════╝  ╚═════╝
```

# Project E.G.O.
### *Electroneural Generative Output*

**A privacy-first, software-defined Brain-Computer Interface that translates thought into action.**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-5-646CFF?style=flat-square&logo=vite&logoColor=white)](https://vitejs.dev)
[![WebSocket](https://img.shields.io/badge/WebSocket-live-00FFCC?style=flat-square)](https://websockets.readthedocs.io)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

</div>

---

## 🧠 What Is E.G.O.?

E.G.O. is a **non-invasive Brain-Computer Interface (BCI)** that uses **SSVEP (Steady-State Visually Evoked Potential)** neural signals to decode human intent and execute system-level actions — without voice, touch, or traditional input.

By focusing your gaze on a flickering stimulus at a specific frequency (10 Hz, 12 Hz, or 15 Hz), your brain resonates at that frequency. E.G.O. captures, isolates, and classifies this neural signal to determine which "mode" you've selected and routes that intent to **Roy**, an embedded local AI agent that executes real-world tasks.

> **Currently showcased as a high-fidelity simulation** using MNE-Python. Hardware-ready design targeting a non-invasive Ear-EEG wearable by Q3 2026.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| **SSVEP Detection** | Steady-State Visually Evoked Potential decoding at 10, 12, and 15 Hz |
| **FFT Analysis** | Real-time Fast Fourier Transform for precision frequency isolation |
| **MNE Brain Mapping** | Minimum Norm Estimate for 3D spatial source localisation |
| **Roy AI Agent** | Local LLM-powered assistant (Llama 3.2 via LM Studio) — no cloud, no telemetry |
| **Live Dashboard** | React + Vite WebSocket-driven neural interface UI |
| **Voice Control** | Wake-word detection ("Ray" / "Roy") with Whisper STT + Silero VAD |
| **Privacy-First** | 100% local execution — brain data never leaves your machine |
| **Ear-EEG Ready** | ADS1299-based hardware design planned for Q3 2026 prototype |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    E.G.O. System Overview                    │
├─────────────────────┬───────────────────────────────────────┤
│   STIMULUS LAYER    │  Three flickering boxes (10/12/15 Hz) │
│                     │  rendered in the React dashboard       │
├─────────────────────┼───────────────────────────────────────┤
│   SIGNAL LAYER      │  MNE-Python simulated EEG source       │
│                     │  (hardware-ready: ADS1299 chipset)     │
├─────────────────────┼───────────────────────────────────────┤
│   PROCESSING LAYER  │  FFT → frequency peak detection        │
│  (Python backend)   │  MNE → 3D spatial brain mapping        │
│                     │  Confidence scoring + mode routing     │
├─────────────────────┼───────────────────────────────────────┤
│   TRANSPORT LAYER   │  WebSocket server (ws://localhost:8766)│
│                     │  Streams: signal_data + freq_detected  │
├─────────────────────┼───────────────────────────────────────┤
│   DASHBOARD LAYER   │  React 18 + Vite + Chart.js            │
│   (ego-dashboard)   │  WaveformChart, FFTChart, EventLog     │
│                     │  ConnectionStatus, FlickerScreen       │
├─────────────────────┼───────────────────────────────────────┤
│   AGENT LAYER       │  ROY v7.9 — Llama 3.2 via LM Studio   │
│   (main.py)         │  Voice commands + system automation    │
└─────────────────────┴───────────────────────────────────────┘

```

## 🚀 Getting Started

### Prerequisites

| Requirement | Version | Purpose |
|---|---|---|
| Python | 3.10+ | Backend agent & signal simulation |
| Node.js | 18+ | Frontend dashboard |
| LM Studio | Latest | Local LLM inference (Llama 3.2-3B) |
| PyAudio | — | Microphone input for voice control |

### 1 — Clone the repository

```bash
git clone https://github.com/Aahaan2007/roy_project.git
cd roy_project
```

### 2 — Install Python dependencies

```bash
pip install numpy mne websockets faster-whisper torch noisereduce \
            pyaudio pyautogui pywhatkit pyttsx3 requests psutil \
            noisereduce screen-brightness-control pystray Pillow \
            pywin32 tkinter
```

Or generate a requirements file after installation:

```bash
pip freeze > requirements.txt
pip install -r requirements.txt
```

### 3 — Start the AI agent + WebSocket server

```bash
python main.py
```

> The Roy agent will boot up, start listening for the wake word "Ray" / "Roy",  
> and open the WebSocket server at `ws://localhost:8766`.

### 4 — Install and run the dashboard

```bash
cd ego-dashboard
npm install
npm run dev
```

Open your browser at **http://localhost:5173**

### 5 — (Optional) Start LM Studio

1. Download [LM Studio](https://lmstudio.ai)
2. Load `llama-3.2-3b-instruct` (or any compatible model)
3. Start the local server on port **1234**
4. Roy will now respond with AI-generated answers to voice queries

---

## 🎙️ Roy Voice Commands

Activate with wake word: **"Ray"** or **"Roy"** (and 60+ phonetic variants)

| Command | Example |
|---|---|
| Open apps | *"Roy, open Chrome"* |
| Web search | *"Roy, search for quantum computing"* |
| Volume | *"Roy, volume up / volume to 60"* |
| Screenshot | *"Roy, take a screenshot"* |
| System info | *"Roy, how's the CPU?"* |
| Time | *"Roy, what time is it?"* |
| Play YouTube | *"Roy, play Bohemian Rhapsody on YouTube"* |
| WhatsApp | *"Roy, message Aahaan on WhatsApp"* |
| Reminders | *"Roy, remind me to drink water in 10 minutes"* |
| Smart chat | *"Roy, explain FFT in one line"* |

---

## 🔬 Technology Stack

### Backend (Python)
| Library | Role |
|---|---|
| `mne` | EEG simulation and 3D brain source mapping |
| `numpy` | FFT computation and signal processing |
| `websockets` | Async WebSocket server |
| `faster-whisper` | On-device speech-to-text (STT) |
| `torch` + `noisereduce` | Neural audio denoising |
| `pyttsx3` | Text-to-speech (TTS) |
| `pyautogui` | System automation (keyboard/mouse) |
| `tkinter` | Animated floating agent dashboard |
| `requests` | LM Studio API calls |

### Frontend (React)
| Library | Role |
|---|---|
| `react` + `react-dom` | UI framework |
| `vite` | Build tool and dev server |
| `react-router-dom` | Client-side routing |
| `chart.js` + `react-chartjs-2` | WaveformChart and FFTChart |

---

<div align="center">

*"Empowering users with a secure, hands-free neural operating system  
that prioritizes data sovereignty and seamless human-AI collaboration."*

**— Project E.G.O.**

</div>
