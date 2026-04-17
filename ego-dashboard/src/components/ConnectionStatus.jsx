/**
 * ConnectionStatus — WebSocket connection indicator pill.
 *
 * Displays a coloured pulsing dot + text label based on connection state.
 * Used inside the Navbar.
 *
 * @param {{ status: 'connected'|'disconnected'|'reconnecting' }} props
 */
export default function ConnectionStatus({ status = 'disconnected' }) {
  const config = {
    connected: {
      dot:   '#00ffcc',
      label: '🟢 Connected',
      cls:   'status-connected',
      pulse: true,
    },
    reconnecting: {
      dot:   '#ffaa33',
      label: '🟡 Reconnecting...',
      cls:   'status-reconnecting',
      pulse: true,
    },
    disconnected: {
      dot:   '#ff5555',
      label: '🔴 Disconnected',
      cls:   'status-disconnected',
      pulse: false,
    },
  }[status] ?? {
    dot:   '#555566',
    label: '⚫ Unknown',
    cls:   '',
    pulse: false,
  };

  return (
    <div className="connection-status">
      <span
        className={`status-dot ${config.pulse ? 'pulse' : ''}`}
        style={{ background: config.dot }}
        aria-hidden="true"
      />
      <span className={config.cls}>{config.label}</span>
    </div>
  );
}
