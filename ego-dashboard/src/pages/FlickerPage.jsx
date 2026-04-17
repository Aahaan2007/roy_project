import { useState, useCallback } from 'react';
import { NavLink }               from 'react-router-dom';
import FlickerScreen             from '../components/FlickerScreen';

/**
 * FlickerPage — Full-viewport SSVEP stimulus display page.
 *
 * Renders the FlickerScreen component on a pure-black (#000) background for
 * maximum luminance contrast, which is required for reliable SSVEP response.
 *
 * Controls:
 *   - "Go Fullscreen" — calls the Fullscreen API on the document element
 *   - "Back to Dashboard" — NavLink to "/"
 */
export default function FlickerPage() {
  const [isFullscreen, setIsFullscreen] = useState(false);

  // ── Fullscreen toggle ────────────────────────────────────────────────────
  const handleFullscreen = useCallback(async () => {
    try {
      if (!document.fullscreenElement) {
        await document.documentElement.requestFullscreen();
        setIsFullscreen(true);
      } else {
        await document.exitFullscreen();
        setIsFullscreen(false);
      }
    } catch (err) {
      // Some browsers (Safari iOS) don't support the Fullscreen API — fail silently
      console.warn('[FlickerPage] Fullscreen not supported:', err);
    }
  }, []);

  return (
    <div className="flicker-page-wrapper">

      {/* ── Top control bar ───────────────────────────────────────────────── */}
      <div className="flicker-controls">
        <NavLink
          to="/"
          className="btn-back"
          aria-label="Back to Dashboard"
        >
          ← Dashboard
        </NavLink>

        <button
          id="btn-fullscreen"
          className="btn btn-ghost"
          onClick={handleFullscreen}
          aria-label={isFullscreen ? 'Exit fullscreen' : 'Enter fullscreen'}
        >
          {isFullscreen ? '⛶ Exit Fullscreen' : '⛶ Go Fullscreen'}
        </button>
      </div>

      {/* ── SSVEP stimulus screen ─────────────────────────────────────────── */}
      <FlickerScreen />

    </div>
  );
}
