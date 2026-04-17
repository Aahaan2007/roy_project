import { useMemo } from 'react';
import {
  Chart as ChartJS,
  BarElement,
  CategoryScale,
  LinearScale,
  Tooltip,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';

ChartJS.register(BarElement, CategoryScale, LinearScale, Tooltip);

// ── Mode → colour map (mirrors the FREQUENCIES constant) ────────────────────
const MODE_COLORS = {
  research: '#4dd0e1',
  navigate: '#64b5f6',
  control:  '#69f0ae',
};

// ── Static chart options — defined outside to keep references stable ─────────
const buildOptions = () => ({
  // 300 ms animation is fine for FFT — it updates ~4–10× per second, not 256 Hz
  animation: { duration: 300 },

  responsive:          true,
  maintainAspectRatio: false,

  scales: {
    x: {
      title: {
        display:  true,
        text:     'Frequency (Hz)',
        color:    '#888899',
        font:     { family: "'JetBrains Mono', monospace", size: 11 },
        padding:  { top: 8 },
      },
      ticks: {
        color:    '#666677',
        font:     { family: "'JetBrains Mono', monospace", size: 10 },
        maxRotation: 0,
        // Only label every 5th bar to avoid crowding (0, 5, 10, 15, 20, 25, 30)
        callback: (_, index) => (index % 5 === 0 ? index : ''),
      },
      grid:   { display: false },
      border: { color: 'rgba(255,255,255,0.06)' },
    },
    y: {
      title: {
        display: true,
        text:    'Power (µV²/Hz)',
        color:   '#888899',
        font:    { family: "'JetBrains Mono', monospace", size: 11 },
      },
      grid: {
        color:     'rgba(255, 255, 255, 0.05)',
        lineWidth: 1,
      },
      ticks: {
        color: '#666677',
        font:  { family: "'JetBrains Mono', monospace", size: 10 },
        maxTicksLimit: 5,
      },
      border: { color: 'rgba(255,255,255,0.06)' },
    },
  },

  plugins: {
    legend: { display: false },
    tooltip: {
      enabled:     true,
      callbacks: {
        title:  (items) => `${items[0].label} Hz`,
        label:  (item)  => ` Power: ${Number(item.raw).toFixed(4)}`,
      },
      backgroundColor: 'rgba(10,10,20,0.9)',
      titleColor:      '#00d4ff',
      bodyColor:       '#aaa',
      borderColor:     'rgba(0,212,255,0.3)',
      borderWidth:     1,
      padding:         10,
      titleFont:       { family: "'JetBrains Mono', monospace", weight: 'bold' },
      bodyFont:        { family: "'JetBrains Mono', monospace" },
    },
  },
});

// Singleton options object — only built once
const CHART_OPTIONS = buildOptions();

/**
 * FFTChart — EEG Power Spectrum bar chart (0–30 Hz).
 *
 * The detected frequency bar lights up in the colour matching its mode,
 * the card glows, and a badge appears below the chart.
 *
 * @param {{ fftData: {power:number[], freqs:number[]}|null,
 *            latestDetection: {frequency:number, confidence:number, mode:string, timestamp:string}|null }} props
 */
export default function FFTChart({ fftData, latestDetection }) {

  // ── Loading / empty state ────────────────────────────────────────────────
  if (!fftData) {
    return (
      <div className="chart-card loading slide-up">
        <span style={{ animation: 'pulse 1.8s ease-in-out infinite', display: 'inline-block' }}>
          ◎
        </span>
        &nbsp; Waiting for FFT data...
      </div>
    );
  }

  // ── Slice to 0–30 Hz window ──────────────────────────────────────────────
  // The backend sends freqs 0-128; we only care about the SSVEP range (0-30)
  const freqSlice  = fftData.freqs.slice(0, 31);
  const powerSlice = fftData.power.slice(0, 31);

  // ── Bar colour logic — memoised on detection changes ────────────────────
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const barColors = useMemo(() => {
    return freqSlice.map((freq) => {
      if (
        latestDetection &&
        Math.abs(freq - latestDetection.frequency) < 1
      ) {
        // Use mode-specific colour if available, fall back to accent cyan
        return MODE_COLORS[latestDetection.mode] ?? '#00d4ff';
      }
      return 'rgba(255, 255, 255, 0.15)';
    });
  // Re-compute whenever detection changes OR the freqSlice changes
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [latestDetection, fftData]);

  // ── Chart data object ────────────────────────────────────────────────────
  const chartData = {
    labels: freqSlice,
    datasets: [
      {
        data:            powerSlice,
        backgroundColor: barColors,
        borderRadius:    4,
        borderSkipped:   false,
        // Highlighted bar gets a subtle border glow via borderColor
        borderColor: barColors.map((c) =>
          c !== 'rgba(255, 255, 255, 0.15)' ? c : 'transparent'
        ),
        borderWidth: 1,
      },
    ],
  };

  // ── Detection badge content ──────────────────────────────────────────────
  const badgeColor = latestDetection
    ? (MODE_COLORS[latestDetection.mode] ?? '#00d4ff')
    : '#00d4ff';

  // ── Render ───────────────────────────────────────────────────────────────
  return (
    <div className={`chart-card slide-up ${latestDetection ? 'glow-active' : ''}`}>
      <h3>📊 Frequency Spectrum (FFT)</h3>

      {/* Live indicator dot in top-right */}
      <div style={{
        position:   'absolute',
        top:        '20px',
        right:      '20px',
        display:    'flex',
        alignItems: 'center',
        gap:        '6px',
        fontFamily: "'JetBrains Mono', monospace",
        fontSize:   '0.7rem',
        color:      'rgba(255,255,255,0.25)',
      }}>
        <span style={{
          width:        '6px',
          height:       '6px',
          borderRadius: '50%',
          background:   fftData ? '#00ffcc' : '#555',
          animation:    fftData ? 'pulseScale 2s ease-in-out infinite' : 'none',
          flexShrink:   0,
        }} />
        0–30 Hz
      </div>

      {/* Bar chart */}
      <div className="fft-container">
        <Bar data={chartData} options={CHART_OPTIONS} />
      </div>

      {/* Detection badge — only shown when a frequency was recently detected */}
      {latestDetection && (
        <div
          className="detection-badge"
          style={{ background: badgeColor }}
        >
          ⚡&nbsp;
          {latestDetection.frequency}Hz — {latestDetection.mode}&nbsp;mode
          &nbsp;
          <span style={{ opacity: 0.7, fontSize: '0.8em' }}>
            (conf:&nbsp;{Number(latestDetection.confidence).toFixed(2)})
          </span>
        </div>
      )}
    </div>
  );
}
