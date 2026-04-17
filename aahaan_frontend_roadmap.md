# 🖥️ Aahaan's Frontend Dashboard — Step-by-Step Implementation Roadmap

> **Project E.G.O.** — Gurgaon Hackathon 2026  
> **Owner:** Aahaan (Co-Founder, Frontend)  
> **Tools:** React, Chart.js / Plotly, CSS Animations, WebSocket

---

## Intro — What Is Aahaan Building?

Aahaan is the **visual storyteller** of Project E.G.O. He builds everything the judges *see*. While Raunak generates fake brain signals in the background and Adibhit runs Nova AI in a terminal — Aahaan's dashboard is what turns invisible data into a **"wow, this actually works"** moment.

He's building **three main pieces:**

| Piece | What It Does | Wow Factor |
|-------|-------------|------------|
| 🔲 **Flicker Screen** | Three boxes flashing at 10/12/15Hz | Simulates what a real SSVEP user would stare at |
| 📊 **Live EEG Dashboard** | Scrolling waveform + FFT bar chart | Real-time brain visualization — the hero screen |
| 🧊 **Hardware Specs Page** | 3D ear-EEG concept render + chip details | Shows judges the product vision beyond software |

```
┌────────────────────────────────────────────────────────────┐
│                   AAHAAN'S DASHBOARD                       │
│                                                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │
│  │ 10Hz     │  │ 12Hz     │  │ 15Hz     │  ← Flicker Grid │
│  │ flicker  │  │ flicker  │  │ flicker  │                  │
│  └──────────┘  └──────────┘  └──────────┘                  │
│                                                            │
│  ┌─────────────────────────────────────┐                   │
│  │ ~~~~ Live EEG Waveform ~~~~~~~~     │  ← Scrolling      │
│  │ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~    │    Chart.js       │
│  └─────────────────────────────────────┘                   │
│                                                            │
│  ┌─────────────────────────────────────┐                   │
│  │  █  █  █████  ← 15Hz bar lights up  │  ← FFT Bar Chart │
│  │  █  █  █████                        │                   │
│  │ 10 12  15  Hz                       │                   │
│  └─────────────────────────────────────┘                   │
│                                                            │
│  ┌─────────────────────────────────────┐                   │
│  │ ⚡ 15Hz detected → control mode     │  ← Event Log     │
│  │ 🟢 Signal streaming...              │                   │
│  └─────────────────────────────────────┘                   │
└────────────────────────────────────────────────────────────┘
```

---

## Step-by-Step Implementation

---

### 📌 Step 1: Project Setup
**⏱ Time: ~20 min** | **Deadline: Phase 1, by 9:00 AM**

- [ ] Scaffold a React app with Vite:
  ```bash
  npx -y create-vite@latest ./ --template react
  npm install
  ```
- [ ] Install dependencies:
  ```bash
  npm install chart.js react-chartjs-2 plotly.js react-plotly.js
  ```
- [ ] Set up the folder structure (see bottom of doc)
- [ ] Create a dark theme CSS foundation in `index.css`:
  - Background: `#0a0a0f` (deep dark)
  - Text: `#e0e0e0`
  - Accent: `#00d4ff` (electric cyan)
  - Cards: `rgba(255,255,255,0.05)` with blur backdrop
- [ ] Import a modern font — **Inter** or **JetBrains Mono** from Google Fonts

> [!TIP]
> Use CSS custom properties (variables) for all colors so you can tweak the look later without hunting through files.

---

### 📌 Step 2: Build the SSVEP Flicker Screen
**⏱ Time: ~45 min** | **Deadline: Phase 1, by 10:30 AM**

This is a web page with **three colored boxes** that flash on/off at precise frequencies. In a real BCI system, a user would stare at one of these to generate SSVEP signals in their brain.

#### How Flicker Works
Each box toggles its `opacity` between `1` and `0` using CSS:
- **10 Hz** = toggle every **50ms** (100ms full cycle)
- **12 Hz** = toggle every **~42ms** (83ms full cycle)
- **15 Hz** = toggle every **~33ms** (66ms full cycle)

#### Implementation
- [ ] Create a `FlickerScreen` component
- [ ] Each box is a `<div>` with a distinct color:

| Frequency | Color | Label |
|-----------|-------|-------|
| 10 Hz | Soft teal `#4dd0e1` | Research Mode |
| 12 Hz | Calm blue `#64b5f6` | Navigate Mode |
| 15 Hz | Bright green `#69f0ae` | Control Mode |

- [ ] Use `useEffect` + `setInterval` to toggle a boolean state at the correct rate
- [ ] Apply `opacity: visible ? 1 : 0` via inline style or CSS class toggle

```jsx
// Pseudocode for one flicker box
function FlickerBox({ frequency, color, label }) {
  const [visible, setVisible] = useState(true);
  
  useEffect(() => {
    const interval = setInterval(() => {
      setVisible(v => !v);
    }, 1000 / (frequency * 2)); // half-period in ms
    return () => clearInterval(interval);
  }, [frequency]);

  return (
    <div className="flicker-box" style={{
      backgroundColor: color,
      opacity: visible ? 1 : 0,
      transition: 'none' // IMPORTANT: no transition for clean flicker
    }}>
      <span className="freq-label">{frequency} Hz</span>
      <span className="mode-label">{label}</span>
    </div>
  );
}
```

- [ ] Style: boxes should be large (at least 200×150px), centered, with spacing
- [ ] Add a header: *"Focus on a box to activate that brain mode"*
- [ ] Add a subtle pulsing border glow on each box to make it feel alive

> [!CAUTION]
> **Epilepsy warning**: Add a dismissible warning banner at the top — *"This page contains flashing elements. Viewer discretion advised."*

---

### 📌 Step 3: Set Up the WebSocket Client
**⏱ Time: ~30 min** | **Deadline: Phase 1, by 11:30 AM**

Connect to Raunak's signal generator to receive live data.

- [ ] Create a custom hook: `useSignalWebSocket(url)`
- [ ] Connect to `ws://localhost:8766` (Raunak's dashboard feed)
- [ ] Parse incoming JSON messages — two types:

**Type 1 — Signal Data (continuous stream):**
```json
{
  "event": "signal_data",
  "samples": [0.12, -0.34, 0.56, ...],
  "fft_power": [0.01, 0.02, 0.87, ...],
  "fft_freqs": [0, 1, 2, ..., 128],
  "timestamp": "2026-04-17T03:15:00"
}
```

**Type 2 — Detection Event (on trigger):**
```json
{
  "event": "frequency_detected",
  "frequency": 15,
  "confidence": 3.72,
  "mode": "control",
  "timestamp": "2026-04-17T03:15:00"
}
```

- [ ] Store in React state:
  - `signalBuffer[]` — rolling array of last ~500 sample points
  - `fftData{}` — latest FFT power/freqs
  - `detectionLog[]` — list of all detection events
  - `connectionStatus` — `"connected"` / `"disconnected"` / `"reconnecting"`

- [ ] Add auto-reconnect logic (retry every 2s on disconnect)
- [ ] Show a connection status indicator in the dashboard header

```jsx
function useSignalWebSocket(url) {
  const [signalBuffer, setSignalBuffer] = useState([]);
  const [fftData, setFftData] = useState(null);
  const [detections, setDetections] = useState([]);
  const [status, setStatus] = useState("disconnecting");

  useEffect(() => {
    let ws;
    const connect = () => {
      ws = new WebSocket(url);
      ws.onopen = () => setStatus("connected");
      ws.onclose = () => {
        setStatus("reconnecting");
        setTimeout(connect, 2000);
      };
      ws.onmessage = (e) => {
        const data = JSON.parse(e.data);
        if (data.event === "signal_data") {
          setSignalBuffer(prev => [...prev.slice(-500), ...data.samples]);
          setFftData({ power: data.fft_power, freqs: data.fft_freqs });
        } else if (data.event === "frequency_detected") {
          setDetections(prev => [data, ...prev].slice(0, 50));
        }
      };
    };
    connect();
    return () => ws?.close();
  }, [url]);

  return { signalBuffer, fftData, detections, status };
}
```

---

### 📌 Step 4: Build the Live EEG Waveform Chart
**⏱ Time: ~45 min** | **Deadline: Phase 2, by 2:30 PM**

A scrolling line chart showing the raw brainwave signal in real time — the classic "hospital monitor" look.

- [ ] Create a `WaveformChart` component using **Chart.js** (`react-chartjs-2`)
- [ ] Chart type: **Line chart** with the following config:

| Setting | Value |
|---------|-------|
| Points shown | Last 256 samples (~1 second at 256Hz) |
| Line color | Electric cyan `#00d4ff` |
| Line width | 1.5px |
| Fill | Subtle gradient below the line |
| Background | Transparent (card bg shows through) |
| Animation | `duration: 0` (must be instant for real-time) |
| X-axis | Hidden (just a scrolling window) |
| Y-axis | Range: -5 to +5 (auto-scale optional) |

- [ ] Update the chart every time `signalBuffer` changes
- [ ] Use `useRef` to avoid re-creating the chart on every render

```jsx
function WaveformChart({ signalBuffer }) {
  const data = {
    labels: signalBuffer.map((_, i) => i),
    datasets: [{
      data: signalBuffer.slice(-256),
      borderColor: '#00d4ff',
      borderWidth: 1.5,
      pointRadius: 0,
      fill: {
        target: 'origin',
        above: 'rgba(0, 212, 255, 0.05)',
      },
      tension: 0.2,
    }]
  };

  const options = {
    animation: { duration: 0 },
    scales: {
      x: { display: false },
      y: { min: -5, max: 5, grid: { color: 'rgba(255,255,255,0.05)' } }
    },
    plugins: { legend: { display: false } }
  };

  return (
    <div className="chart-card">
      <h3>🧠 Live Neural Signal</h3>
      <Line data={data} options={options} />
    </div>
  );
}
```

> [!IMPORTANT]
> Set `animation.duration = 0` — otherwise Chart.js tries to animate every data update, causing massive lag and frame drops on real-time data.

---

### 📌 Step 5: Build the FFT Power Spectrum Bar Chart
**⏱ Time: ~45 min** | **Deadline: Phase 2, by 4:00 PM**

A bar chart showing the frequency breakdown. The **detected frequency bar lights up** — this is the "wow" moment for judges.

- [ ] Create a `FFTChart` component using Chart.js **Bar chart**
- [ ] Show bars for frequencies 0–30 Hz (relevant EEG range)
- [ ] Default bar color: dim grey `rgba(255,255,255,0.15)`
- [ ] **Highlight logic:** When a `frequency_detected` event arrives:
  - The bar at that frequency → turns **bright electric blue** `#00d4ff`
  - Add a glow effect (CSS `box-shadow` on the canvas container)
  - Show a floating label: *"15Hz — Control Mode Activated!"*
  - Fade back to normal after 2 seconds

```jsx
function FFTChart({ fftData, latestDetection }) {
  if (!fftData) return <div className="chart-card loading">Waiting for data...</div>;

  const barColors = fftData.freqs.map(freq => {
    if (latestDetection && Math.abs(freq - latestDetection.frequency) < 1) {
      return '#00d4ff'; // HIGHLIGHT detected frequency
    }
    return 'rgba(255, 255, 255, 0.15)';
  });

  const data = {
    labels: fftData.freqs.slice(0, 31), // 0-30 Hz
    datasets: [{
      data: fftData.power.slice(0, 31),
      backgroundColor: barColors.slice(0, 31),
      borderRadius: 4,
    }]
  };

  const options = {
    animation: { duration: 300 },
    scales: {
      x: { title: { display: true, text: 'Frequency (Hz)', color: '#888' }},
      y: { title: { display: true, text: 'Power', color: '#888' }, grid: { color: 'rgba(255,255,255,0.05)' }}
    },
    plugins: { legend: { display: false } }
  };

  return (
    <div className={`chart-card ${latestDetection ? 'glow-active' : ''}`}>
      <h3>📊 Frequency Spectrum (FFT)</h3>
      <Bar data={data} options={options} />
      {latestDetection && (
        <div className="detection-badge">
          ⚡ {latestDetection.frequency}Hz — {latestDetection.mode} mode
        </div>
      )}
    </div>
  );
}
```

**CSS glow effect:**
```css
.chart-card.glow-active {
  box-shadow: 0 0 30px rgba(0, 212, 255, 0.3), 
              0 0 60px rgba(0, 212, 255, 0.1);
  border-color: #00d4ff;
  transition: box-shadow 0.3s ease, border-color 0.3s ease;
}
```

---

### 📌 Step 6: Build the Nova Event Log Panel
**⏱ Time: ~30 min** | **Deadline: Phase 2, by 5:00 PM**

A live feed showing every time Nova receives a brain command and what it did.

- [ ] Create an `EventLog` component
- [ ] Displays a scrolling list of detection events, newest first
- [ ] Each entry shows:
  - Timestamp
  - Detected frequency + mode
  - Confidence score
  - Status indicator (green dot = sent, yellow = pending)

```jsx
function EventLog({ detections }) {
  return (
    <div className="event-log">
      <h3>⚡ Neural Command Log</h3>
      <div className="log-entries">
        {detections.map((d, i) => (
          <div key={i} className={`log-entry mode-${d.mode}`}>
            <span className="dot" />
            <span className="time">{new Date(d.timestamp).toLocaleTimeString()}</span>
            <span className="freq">{d.frequency}Hz</span>
            <span className="mode">{d.mode}</span>
            <span className="conf">conf: {d.confidence}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
```

- [ ] Color-code by mode:
  - Research (10Hz) → teal
  - Navigate (12Hz) → blue
  - Control (15Hz) → green

---

### 📌 Step 7: Assemble the Main Dashboard Layout
**⏱ Time: ~30 min** | **Deadline: Phase 2, by 6:00 PM**

Wire all components into one cohesive page.

- [ ] Create a `Dashboard` page component
- [ ] Layout using **CSS Grid**:

```
┌─────────────────────────────────────────────┐
│  HEADER: E.G.O. Dashboard  [🟢 Connected]  │
├─────────────────────────────────────────────┤
│  ┌────────┐  ┌────────┐  ┌────────┐        │
│  │ 10Hz   │  │ 12Hz   │  │ 15Hz   │ ROW 1  │
│  └────────┘  └────────┘  └────────┘        │
├─────────────────────────────────────────────┤
│  ┌──────────────────────────────────┐       │
│  │  EEG Waveform (full width)       │ ROW 2 │
│  └──────────────────────────────────┘       │
├──────────────────────┬──────────────────────┤
│  ┌─────────────────┐ │ ┌──────────────────┐ │
│  │  FFT Bar Chart  │ │ │  Event Log       │ │ ROW 3
│  └─────────────────┘ │ └──────────────────┘ │
└──────────────────────┴──────────────────────┘
```

- [ ] Add a **navigation bar** to switch between:
  - 📊 Dashboard (main view)
  - 🔲 Flicker Screen (full-screen mode for demos)
  - 🧊 Hardware Specs (concept page)
- [ ] Use React Router or simple state toggle for page switching

---

### 📌 Step 8: Build the Hardware Specs / Vision Page
**⏱ Time: ~30 min** | **Deadline: Phase 3, by 8:00 PM**

A concept page showing judges what the *real* product would look like with actual EEG hardware.

- [ ] Create a `HardwareSpecs` page
- [ ] Content sections:

| Section | Content |
|---------|---------|
| **Hero** | "The E.G.O. Ear" — 3D concept render of ear-mounted EEG sensor |
| **Chip** | ADS1299 specs — 8-channel, 24-bit, medical-grade |
| **Comparison** | Table: Our approach vs. Neuralink vs. OpenBCI |
| **Roadmap** | Timeline: Software ✅ → Prototype → Clinical trial |
| **Cost** | Estimated BOM: ~$500 for prototype |

- [ ] Use smooth scroll sections with fade-in animations
- [ ] Add a 3D-looking render of the ear device (can be a generated image or illustration)
- [ ] This page is **not connected to live data** — it's pure presentation

---

### 📌 Step 9: Responsive Design & Visual Polish
**⏱ Time: ~45 min** | **Deadline: Phase 3, by 10:00 PM**

Make everything look premium and work on different screens.

- [ ] **Responsive breakpoints:**
  - Desktop (>1024px): Full grid layout
  - Tablet (768-1024px): Stack charts vertically
  - Mobile (<768px): Single column, smaller flicker boxes

- [ ] **Micro-animations to add:**
  - Dashboard cards: subtle slide-up on mount (`transform + opacity`)
  - Connection status: pulsing dot animation
  - Detection event: brief flash/shake on the FFT chart card
  - Flicker boxes: subtle border glow pulse

- [ ] **Typography polish:**
  - Headers: `JetBrains Mono` (techy feel)
  - Body: `Inter` (clean readability)
  - Numbers/data: `monospace`

- [ ] **Glassmorphism cards:**
  ```css
  .chart-card {
    background: rgba(255, 255, 255, 0.03);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 24px;
  }
  ```

- [ ] Add the **E.G.O. logo** and project branding in the header
- [ ] Add a **dark/light mode toggle** (stretch goal, dark-first)

---

### 📌 Step 10: Testing & Validation
**⏱ Time: ~30 min** | **Deadline: Phase 3, by 11:00 PM**

#### Flicker Screen Tests
- [ ] **Frequency accuracy test:** Use browser DevTools Performance tab to verify the boxes are toggling at the correct intervals
  - 10Hz box: toggle every ~50ms
  - 12Hz box: toggle every ~42ms
  - 15Hz box: toggle every ~33ms
- [ ] **Visual test:** Record a slow-mo video on phone → count flickers per second
- [ ] **Epilepsy warning** is visible and dismissible

#### WebSocket Tests
- [ ] Dashboard shows `🟢 Connected` when Raunak's script is running
- [ ] Dashboard shows `🔴 Disconnected` + auto-retries when script is stopped
- [ ] Data flows within ~100ms of Raunak sending it

#### Chart Tests
- [ ] **Waveform chart:** Scrolls smoothly without lag (check for frame drops)
- [ ] **FFT chart:** Bars update in real-time, detected frequency bar highlights correctly
- [ ] **No memory leaks:** Dashboard runs for 5+ minutes without slowing down
  - Check with Chrome DevTools → Memory tab → take heap snapshots

#### Integration Test (with Raunak)
- [ ] Raunak starts `signal_generator.py`
- [ ] Aahaan opens dashboard in browser
- [ ] Waveform shows noisy pink noise baseline
- [ ] Raunak presses `3` → waveform shows stronger oscillations
- [ ] FFT chart: 15Hz bar lights up bright cyan
- [ ] Event log shows: *"⚡ 15Hz — Control Mode"*
- [ ] Raunak releases key → signal returns to noise → 15Hz bar dims

#### Browser Compatibility
- [ ] Test on Chrome (primary)
- [ ] Test on Firefox (backup)
- [ ] Full-screen mode works for flicker screen presentation

---

## File Structure

```
ego-dashboard/
├── public/
│   └── index.html
├── src/
│   ├── App.jsx                 # Main app + routing
│   ├── index.css               # Global styles, CSS variables, fonts
│   │
│   ├── hooks/
│   │   └── useSignalWebSocket.js   # WebSocket connection + state
│   │
│   ├── components/
│   │   ├── FlickerBox.jsx          # Single flicker box
│   │   ├── FlickerScreen.jsx       # Grid of 3 flicker boxes
│   │   ├── WaveformChart.jsx       # Live EEG line chart
│   │   ├── FFTChart.jsx            # Frequency spectrum bar chart
│   │   ├── EventLog.jsx            # Nova detection log
│   │   ├── ConnectionStatus.jsx    # WebSocket status indicator
│   │   └── Navbar.jsx              # Navigation bar
│   │
│   ├── pages/
│   │   ├── Dashboard.jsx           # Main dashboard (waveform + FFT + log)
│   │   ├── FlickerPage.jsx         # Full-screen flicker for demos
│   │   └── HardwareSpecs.jsx       # Vision page with 3D concept
│   │
│   └── utils/
│       └── constants.js            # Colors, frequencies, WS URLs
│
├── package.json
└── README.md
```

---

## Integration Points

| From → To | What | Channel |
|-----------|------|---------|
| **Raunak → Aahaan** | Raw signal samples + FFT data | WebSocket `ws://localhost:8766` |
| **Raunak → Aahaan** | Frequency detection events | Same WebSocket, different `event` type |
| **Aahaan → Adibhit** | No direct connection (Nova events shown via Raunak's relay) | — |
| **Dhairya → Aahaan** | Bridge testing, UI feedback | Manual |

---

## Hackathon Day Timeline with Deadlines

| Phase | Time | Aahaan's Tasks | Deadline |
|-------|------|---------------|----------|
| **Phase 1** | 8:30 AM – 1:00 PM | Step 1 (setup) + Step 2 (flicker screen) + Step 3 (WebSocket) | **✅ Flicker screen working by 12:00 PM** |
| **Phase 2** | 1:00 PM – 7:00 PM | Step 4 (waveform) + Step 5 (FFT) + Step 6 (event log) + Step 7 (layout) | **✅ Live dashboard receiving data by 6:00 PM** |
| **Phase 3** | 7:00 PM – 12:00 AM | Step 8 (hardware page) + Step 9 (polish) + Step 10 (testing) | **✅ Full UI polished by 11:00 PM** |
| **Phase 4** | After midnight – 8 AM | Bug fixing, dry run with full team, presentation prep | **✅ Zero crashes during demo rehearsal** |

---

## Demo-Day Checklist

- [ ] Flicker screen runs full-screen on the presentation laptop
- [ ] Dashboard shows live waveform scrolling
- [ ] When Raunak triggers 15Hz → FFT bar lights up + event appears in log
- [ ] Hardware specs page loads with concept renders
- [ ] No console errors in browser
- [ ] Dashboard runs for 10+ minutes without memory issues
- [ ] Epilepsy warning is shown before flicker screen

> **The "Oh Wow" Moment:** Judges see three flickering boxes, a live brainwave scrolling across the screen, and the moment someone "thinks" at 15Hz — the FFT bar erupts in cyan, the event log updates, and Nova starts executing commands. All in real-time. That's Aahaan's masterpiece. 🎨
