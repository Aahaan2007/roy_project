import { useState, useEffect, useRef } from 'react';

/**
 * FlickerBox — A single SSVEP stimulus box that flashes at a precise frequency.
 *
 * CRITICAL: transition must be "none" on the flicker element.
 * Any CSS transition will blur the hard on/off edge, destroying frequency accuracy.
 *
 * @param {number}  frequency  - Hz (e.g. 10, 12, 15)
 * @param {string}  color      - CSS hex color for the box background
 * @param {string}  label      - Mode label (e.g. "Research Mode")
 */
export default function FlickerBox({ frequency, color, label }) {
  const [visible, setVisible] = useState(true);

  // Track actual measured fps for debug overlay (optional)
  const toggleCount = useRef(0);
  const lastTime    = useRef(performance.now());

  useEffect(() => {
    // Half-period in ms: at 10 Hz → 50 ms, 12 Hz → ~41.67 ms, 15 Hz → ~33.33 ms
    const halfPeriodMs = 1000 / (frequency * 2);

    const interval = setInterval(() => {
      setVisible(v => !v);
      toggleCount.current += 1;
    }, halfPeriodMs);

    return () => clearInterval(interval);
  }, [frequency]);

  // ------------------------------------------------------------------
  // Ambient glow container (always visible, independent of flicker)
  // The glow uses the box color so each frequency has its own hue.
  // ------------------------------------------------------------------
  const glowStyle = {
    position:     'relative',
    borderRadius: '16px',
    padding:      '3px',                          // glow "ring" thickness
    background:   `${color}22`,                   // very transparent version of color
    boxShadow:    `0 0 24px ${color}55, 0 0 48px ${color}22`,
    animation:    'glowBreath 2.4s ease-in-out infinite',
    animationDelay: `${(frequency % 3) * 0.4}s`, // stagger so all 3 boxes don't pulse together
  };

  // ------------------------------------------------------------------
  // The actual flickering element — MUST have transition: 'none'
  // ------------------------------------------------------------------
  const boxStyle = {
    backgroundColor: color,
    opacity:         visible ? 1 : 0,
    transition:      'none',                      // ← CRITICAL
    borderRadius:    '14px',
    width:           '220px',
    height:          '155px',
    display:         'flex',
    flexDirection:   'column',
    alignItems:      'center',
    justifyContent:  'center',
    gap:             '6px',
    cursor:          'default',
    userSelect:      'none',
  };

  const freqLabelStyle = {
    fontFamily:  "'JetBrains Mono', monospace",
    fontSize:    '2.2rem',
    fontWeight:  '700',
    color:       'rgba(0, 0, 0, 0.80)',
    lineHeight:  '1',
    letterSpacing: '-1px',
  };

  const modeLabelStyle = {
    fontFamily:     "'Inter', sans-serif",
    fontSize:       '0.72rem',
    fontWeight:     '600',
    color:          'rgba(0, 0, 0, 0.60)',
    textTransform:  'uppercase',
    letterSpacing:  '1.5px',
    marginTop:      '4px',
  };

  return (
    <div style={glowStyle}>
      <div style={boxStyle}>
        <span style={freqLabelStyle}>{frequency} Hz</span>
        <span style={modeLabelStyle}>{label}</span>
      </div>
    </div>
  );
}
