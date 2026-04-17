import { useMemo } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Filler,
} from 'chart.js';
import { Line } from 'react-chartjs-2';

// Register once at module level — safe to call multiple times (Chart.js is idempotent)
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Filler);

// ── Static labels array — pre-built, never changes ──────────────────────────
// Avoids rebuilding 256 strings on every render / every data tick
const LABELS = Array.from({ length: 256 }, (_, i) => i);

// ── Static chart options — defined outside the component ────────────────────
// Keeps the options object reference stable so Chart.js doesn't re-initialise
// the chart on every render.
const CHART_OPTIONS = {
  // CRITICAL: animation must be 0 — any non-zero duration causes Chart.js to
  // queue a new animation on every data update, resulting in massive frame drops
  // at 256 Hz signal rates.
  animation: { duration: 0 },

  responsive:          true,
  maintainAspectRatio: false,

  interaction: {
    mode:      'index',
    intersect: false,
  },

  scales: {
    x: {
      display: false, // timestamp axis is meaningless for a scrolling window
    },
    y: {
      min:  -5,
      max:   5,
      grid: {
        color:     'rgba(255, 255, 255, 0.05)',
        lineWidth: 1,
      },
      ticks: {
        color:    '#555566',
        font:     { family: "'JetBrains Mono', monospace", size: 10 },
        maxTicksLimit: 6,
        callback: (v) => `${v > 0 ? '+' : ''}${v}µV`,
      },
      border: { color: 'rgba(255,255,255,0.06)' },
    },
  },

  plugins: {
    legend:  { display: false },
    tooltip: { enabled: false }, // tooltips cause jank on high-frequency updates
  },

  elements: {
    line: { borderCapStyle: 'round' },
  },
};

/**
 * WaveformChart — Real-time scrolling EEG waveform.
 *
 * Renders the last 256 samples from the signal buffer as a smooth cyan line
 * with a subtle fill below, styled to look like a medical grade oscilloscope.
 *
 * @param {{ signalBuffer: number[] }} props
 */
export default function WaveformChart({ signalBuffer }) {

  // ── Slice the last 256 samples — memoised to avoid object churn ──────────
  const chartData = useMemo(() => {
    const window256 = signalBuffer.slice(-256);

    return {
      labels: LABELS.slice(0, window256.length),
      datasets: [
        {
          data:        window256,
          borderColor: '#00d4ff',
          borderWidth: 1.5,
          pointRadius: 0,         // no dots — they tank performance on dense data
          fill: {
            target: 'origin',
            above:  'rgba(0, 212, 255, 0.05)',
            below:  'rgba(255, 79, 207, 0.03)', // subtle pink tint for negative excursions
          },
          tension:      0.2,
          cubicInterpolationMode: 'monotone',
        },
      ],
    };
  }, [signalBuffer]);

  // ── Empty state ───────────────────────────────────────────────────────────
  if (!signalBuffer || signalBuffer.length === 0) {
    return (
      <div className="chart-card slide-up">
        <h3>🧠 Live Neural Signal</h3>
        <div className="waveform-placeholder">
          <span style={{ animation: 'pulse 1.8s ease-in-out infinite', display: 'inline-block' }}>
            ◎
          </span>
          &nbsp; Waiting for neural signal...
        </div>
      </div>
    );
  }

  // ── Live chart ────────────────────────────────────────────────────────────
  return (
    <div className="chart-card slide-up">
      <h3>🧠 Live Neural Signal</h3>

      {/* Sample count badge */}
      <div style={{
        position:    'absolute',
        top:         '20px',
        right:       '20px',
        fontFamily:  "'JetBrains Mono', monospace",
        fontSize:    '0.7rem',
        color:       'rgba(0, 212, 255, 0.45)',
        letterSpacing: '0.5px',
      }}>
        {signalBuffer.length} samples
      </div>

      {/* Chart wrapper — fixed height is required when maintainAspectRatio is false */}
      <div className="waveform-container">
        <Line data={chartData} options={CHART_OPTIONS} />
      </div>
    </div>
  );
}
