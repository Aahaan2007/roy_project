import { useState } from 'react';
import FlickerBox from './FlickerBox';
import { FREQUENCIES } from '../utils/constants';

/**
 * FlickerScreen — Full SSVEP stimulus display.
 *
 * Shows an epilepsy warning, a header, and three FlickerBox components
 * flashing at 10 Hz, 12 Hz, and 15 Hz respectively.
 *
 * The warning banner is dismissible via useState.
 */
export default function FlickerScreen() {
  const [warningVisible, setWarningVisible] = useState(true);

  return (
    <div className="flicker-screen">

      {/* ── Epilepsy Warning Banner ───────────────────────────────────────── */}
      {warningVisible && (
        <div className="epilepsy-warning">
          <span>
            ⚠️ &nbsp;
            <strong>Photosensitivity warning:</strong>{' '}
            This screen contains rapidly flashing elements. If you have epilepsy
            or are sensitive to flashing lights, please look away.
          </span>
          <button
            className="warn-dismiss"
            onClick={() => setWarningVisible(false)}
            aria-label="Dismiss warning"
          >
            Dismiss ✕
          </button>
        </div>
      )}

      {/* ── Header ───────────────────────────────────────────────────────── */}
      <div className="flicker-header">
        <h2 className="slide-up">SSVEP Stimulus Grid</h2>
        <p className="slide-up-d1">
          Focus on a box to activate that brain mode — your EEG will show a peak
          at the corresponding frequency.
        </p>
      </div>

      {/* ── Frequency Labels Row ─────────────────────────────────────────── */}
      <div className="flicker-freq-labels slide-up-d2">
        {FREQUENCIES.map(({ hz, color, label }) => (
          <div key={hz} className="freq-info-chip" style={{ borderColor: `${color}55` }}>
            <span className="chip-dot" style={{ background: color }} />
            <span className="chip-hz"  style={{ color }}>{hz} Hz</span>
            <span className="chip-label">{label}</span>
          </div>
        ))}
      </div>

      {/* ── The Three Flicker Boxes ───────────────────────────────────────── */}
      <div className="flicker-grid slide-up-d3">
        {FREQUENCIES.map(({ hz, color, label }) => (
          <FlickerBox
            key={hz}
            frequency={hz}
            color={color}
            label={label}
          />
        ))}
      </div>

      {/* ── Footer note ──────────────────────────────────────────────────── */}
      <p className="flicker-footer-note slide-up-d4">
        🧠 Signal streaming to dashboard in real-time via WebSocket
      </p>

    </div>
  );
}
