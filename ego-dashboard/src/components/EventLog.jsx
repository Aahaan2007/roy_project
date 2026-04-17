import { useRef, useEffect } from 'react';

// ── Mode → display colour map ────────────────────────────────────────────────
const MODE_DOT_COLOR = {
  research: '#4dd0e1',
  navigate: '#64b5f6',
  control:  '#69f0ae',
};

// Capitalise first letter, handle undefined gracefully
const capitalize = (str = '') =>
  str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();

// Format timestamp — falls back to raw string if Date parsing fails
const formatTime = (ts) => {
  try {
    return new Date(ts).toLocaleTimeString([], {
      hour:        '2-digit',
      minute:      '2-digit',
      second:      '2-digit',
      hour12:      false,
    });
  } catch {
    return ts ?? '—';
  }
};

/**
 * EventLog — Scrolling list of SSVEP frequency detection events.
 *
 * Detections arrive newest-first from the hook. The list auto-scrolls
 * to the top whenever a new event is prepended.
 *
 * @param {{ detections: Array<{frequency, confidence, mode, timestamp}> }} props
 */
export default function EventLog({ detections = [] }) {
  const listRef = useRef(null);

  // Scroll to top whenever a new detection is prepended
  // (detections[0] changes identity when a new event arrives)
  useEffect(() => {
    if (listRef.current && detections.length > 0) {
      listRef.current.scrollTop = 0;
    }
  }, [detections[0]]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="chart-card event-log slide-up">
      {/* ── Header ──────────────────────────────────────────────────────── */}
      <h3>⚡ Neural Command Log</h3>

      {/* ── Count badge ─────────────────────────────────────────────────── */}
      <div style={{
        position:   'absolute',
        top:        '20px',
        right:      '20px',
        fontFamily: "'JetBrains Mono', monospace",
        fontSize:   '0.7rem',
        color:      detections.length > 0 ? 'rgba(0,212,255,0.5)' : 'rgba(255,255,255,0.15)',
        transition: 'color 0.3s ease',
      }}>
        {detections.length} / 50
      </div>

      {/* ── Log entries ─────────────────────────────────────────────────── */}
      {detections.length === 0 ? (
        <div className="log-empty">
          <span style={{ animation: 'pulse 2.4s ease-in-out infinite', display: 'inline-block' }}>
            ◌
          </span>
          &nbsp;&nbsp;No neural commands detected yet...
        </div>
      ) : (
        <div className="log-entries" ref={listRef}>
          {detections.map((d, i) => {
            const dotColor = MODE_DOT_COLOR[d.mode] ?? '#888';
            const isNewest = i === 0;

            return (
              <div
                key={`${d.timestamp}-${i}`}
                className={`log-entry mode-${d.mode}`}
                style={{
                  // Newest entry gets a fresh fadeIn; older entries keep their
                  // last rendered state (no re-animation on scroll)
                  animation: isNewest
                    ? 'slideInLeft 0.3s ease forwards'
                    : 'none',
                  // Newest entry gets a faint background highlight that fades
                  background: isNewest
                    ? `${dotColor}10`   // 6% opacity version of mode colour
                    : 'transparent',
                }}
              >
                {/* Coloured mode dot */}
                <span
                  className="dot"
                  style={{
                    background: dotColor,
                    boxShadow:  isNewest ? `0 0 6px ${dotColor}88` : 'none',
                  }}
                />

                {/* Timestamp */}
                <span className="time">{formatTime(d.timestamp)}</span>

                {/* Frequency */}
                <span className="freq" style={{ color: dotColor }}>
                  {d.frequency}Hz
                </span>

                {/* Mode label */}
                <span className="mode">{capitalize(d.mode)}</span>

                {/* Confidence score — right-aligned */}
                <span className="conf">
                  conf:&nbsp;{typeof d.confidence === 'number'
                    ? d.confidence.toFixed(2)
                    : '—'}
                </span>
              </div>
            );
          })}
        </div>
      )}

      {/* ── Footer: clear indicator when close to cap ───────────────────── */}
      {detections.length >= 40 && (
        <div style={{
          marginTop:  '10px',
          fontSize:   '0.7rem',
          color:      'rgba(255,170,0,0.5)',
          fontFamily: "'JetBrains Mono', monospace",
          textAlign:  'center',
        }}>
          ⚠ Log nearing capacity ({detections.length}/50)
        </div>
      )}
    </div>
  );
}
