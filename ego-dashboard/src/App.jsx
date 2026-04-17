import { BrowserRouter, Routes, Route } from 'react-router-dom';

import Navbar        from './components/Navbar';
import Dashboard     from './pages/Dashboard';
import FlickerPage   from './pages/FlickerPage';
import HardwareSpecs from './pages/HardwareSpecs';

import useSignalWebSocket from './hooks/useSignalWebSocket';

import './index.css';

/**
 * App — Root shell for the E.G.O. Neural Interface Dashboard.
 *
 * The WebSocket hook lives HERE (single source of truth) so that:
 *   • The Navbar always sees the live connection status
 *   • Dashboard receives data as props — no second WebSocket connection
 *   • Navigating between pages never re-mounts the hook or re-opens the socket
 *
 * Data flow:
 *   useSignalWebSocket → { signalBuffer, fftData, detections, status }
 *     ├─ status          → <Navbar connectionStatus={status} />
 *     └─ all four fields → <Dashboard ... /> (via Route element prop)
 */
export default function App() {
  const { signalBuffer, fftData, detections, status } = useSignalWebSocket();

  return (
    <BrowserRouter>
      {/* Sticky top bar — always visible on every page */}
      <Navbar connectionStatus={status} />

      {/* Page content */}
      <Routes>
        {/* Dashboard receives live signal data as props */}
        <Route
          path="/"
          element={
            <Dashboard
              signalBuffer={signalBuffer}
              fftData={fftData}
              detections={detections}
              status={status}
            />
          }
        />

        <Route path="/flicker"  element={<FlickerPage />}   />
        <Route path="/hardware" element={<HardwareSpecs />}  />
      </Routes>
    </BrowserRouter>
  );
}
