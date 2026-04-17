import { NavLink } from 'react-router-dom';
import ConnectionStatus from './ConnectionStatus';

/**
 * Navbar — Sticky top navigation bar for the E.G.O. dashboard.
 *
 * Left:   Branding (E.G.O. logo + subtitle)
 * Center: ConnectionStatus indicator
 * Right:  Page navigation links
 *
 * NavLink automatically adds the "active" class when its route matches,
 * which our CSS uses to highlight the current page.
 *
 * @param {{ connectionStatus: 'connected'|'disconnected'|'reconnecting' }} props
 */
export default function Navbar({ connectionStatus = 'disconnected' }) {
  return (
    <nav className="navbar" role="navigation" aria-label="Main navigation">

      {/* ── Brand ──────────────────────────────────────────────────────── */}
      <div className="navbar-brand">
        <span className="logo-text" aria-label="Project E.G.O.">E.G.O.</span>
        <span className="logo-subtitle">Neural Interface Dashboard</span>
      </div>

      {/* ── Connection status (center) ─────────────────────────────────── */}
      <div className="navbar-center">
        <ConnectionStatus status={connectionStatus} />
      </div>

      {/* ── Nav links (right) ──────────────────────────────────────────── */}
      <div className="nav-links" role="menubar">
        <NavLink
          to="/"
          end                          /* `end` makes "/" only active on exact match */
          className={({ isActive }) =>
            `nav-link${isActive ? ' active' : ''}`
          }
          role="menuitem"
        >
          📊 Dashboard
        </NavLink>

        <NavLink
          to="/flicker"
          className={({ isActive }) =>
            `nav-link${isActive ? ' active' : ''}`
          }
          role="menuitem"
        >
          🔲 Flicker
        </NavLink>

        <NavLink
          to="/hardware"
          className={({ isActive }) =>
            `nav-link${isActive ? ' active' : ''}`
          }
          role="menuitem"
        >
          🧊 Hardware
        </NavLink>
      </div>

    </nav>
  );
}
