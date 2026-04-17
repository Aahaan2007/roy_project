import { useState, useEffect } from 'react';
import WaveformChart from '../components/WaveformChart';
import FFTChart      from '../components/FFTChart';
import EventLog      from '../components/EventLog';

// How long the "latest detection" glow / badge lingers after a new event (ms)
const DETECTION_TTL_MS = 2000;

/**
 * Dashboard — Main page of the E.G.O. neural interface dashboard.
 *
 * Layout (CSS Grid):
 *   Row 1 — Stats bar  : live counters for samples, FFT state, and detections
 *   Row 2 — Waveform   : full-width scrolling EEG signal (WaveformChart)
 *   Row 3 — Split 3/2  : FFTChart (left) + EventLog (right)
 *
 * Data is received as props from App.jsx, which owns the single
 * useSignalWebSocket hook — no second WebSocket connection is opened here.
 *
 * @param {{ signalBuffer: number[], fftData: object|null,
 *            detections: object[], status: string }} props
 */
export default function Dashboard({ signalBuffer, fftData, detections, status }) {

  // ── Ephemeral "latest detection" with 2-second auto-clear ────────────────
  const [latestDetection, setLatestDetection] = useState(null);

  useEffect(() => {
    if (detections.length === 0) return;

    // Promote the newest detection immediately
    setLatestDetection(detections[0]);

    // Schedule automatic clear after TTL so glow/badge fades away
    const timer = setTimeout(() => setLatestDetection(null), DETECTION_TTL_MS);
    return () => clearTimeout(timer);
  }, [detections[0]]); // eslint-disable-line react-hooks/exhaustive-deps
  // ↑ Intentionally use the first element as the dependency — changes only
  //   when a genuinely new event is prepended (same pattern as EventLog).

  // ── Derived stats for the top bar ────────────────────────────────────────
  const fftStatus    = fftData ? 'Active' : 'Waiting';
  const lastDetLabel = detections[0]
    ? `${detections[0].frequency}Hz · ${detections[0].mode}`
    : '—';

  // ── Render ───────────────────────────────────────────────────────────────
  return (
    <div className="dashboard-wrapper">
      <div className="dashboard-grid">

        {/* ── Row 1: Stats bar ───────────────────────────────────────────── */}
        <div
          className="dashboard-stats-bar slide-up"
          role="status"
          aria-live="polite"
          aria-label="Live signal statistics"
        >
          {/* Samples received */}
          <div className={`stat-pill ${signalBuffer.length > 0 ? 'active' : ''}`}>
            <span aria-hidden="true">📡</span>
            <span>Samples</span>
            <span className="stat-value">{signalBuffer.length}</span>
          </div>

          {/* FFT state */}
          <div className={`stat-pill ${fftData ? 'active' : ''}`}>
            <span aria-hidden="true">📊</span>
            <span>FFT</span>
            <span className="stat-value">{fftStatus}</span>
          </div>

          {/* Detection count */}
          <div className={`stat-pill ${detections.length > 0 ? 'active' : ''}`}>
            <span aria-hidden="true">⚡</span>
            <span>Detections</span>
            <span className="stat-value">{detections.length}</span>
          </div>

          {/* Most recent detection summary */}
          <div className={`stat-pill ${latestDetection ? 'active' : ''}`}>
            <span aria-hidden="true">🎯</span>
            <span>Last</span>
            <span className="stat-value">{lastDetLabel}</span>
          </div>

          {/* Connection status pill — mirrors the navbar pill in compact form */}
          <div
            className="stat-pill"
            style={{
              marginLeft:  'auto',
              borderColor: status === 'connected'
                ? 'rgba(0,255,204,0.35)'
                : status === 'reconnecting'
                  ? 'rgba(255,170,0,0.35)'
                  : 'rgba(255,68,68,0.3)',
            }}
          >
            <span
              style={{
                width:        '7px',
                height:       '7px',
                borderRadius: '50%',
                background:   status === 'connected'
                  ? '#00ffcc'
                  : status === 'reconnecting'
                    ? '#ffaa00'
                    : '#ff4444',
                flexShrink:   0,
                animation:    status !== 'disconnected'
                  ? 'pulseScale 1.8s ease-in-out infinite'
                  : 'none',
              }}
              aria-hidden="true"
            />
            <span style={{
              color: status === 'connected'
                ? '#00ffcc'
                : status === 'reconnecting'
                  ? '#ffaa00'
                  : '#ff4444',
            }}>
              {status === 'connected'
                ? 'Connected'
                : status === 'reconnecting'
                  ? 'Reconnecting…'
                  : 'Disconnected'}
            </span>
          </div>
        </div>

        {/* ── Row 2: Full-width waveform ─────────────────────────────────── */}
        <WaveformChart signalBuffer={signalBuffer} />

        {/* ── Row 3: FFT (left 3fr) + Event log (right 2fr) ─────────────── */}
        <div className="dashboard-row-split">
          <FFTChart
            fftData={fftData}
            latestDetection={latestDetection}
          />
          <EventLog detections={detections} />
        </div>

      </div>
    </div>
  );
}
