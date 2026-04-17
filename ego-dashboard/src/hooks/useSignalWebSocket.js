import { useState, useEffect, useRef, useCallback } from 'react';
import { WEBSOCKET_URL } from '../utils/constants';

/**
 * useSignalWebSocket — Custom hook for the E.G.O. EEG signal stream.
 *
 * Maintains a persistent WebSocket connection to Raunak's signal generator
 * and manages all derived state: raw signal buffer, FFT data, detection log,
 * and connection status.
 *
 * Auto-reconnects every 2 s on unexpected disconnect.
 * Uses refs everywhere inside the connect closure to avoid stale state traps.
 *
 * @param {string} url - WebSocket server URL (defaults to ws://localhost:8766)
 * @returns {{ signalBuffer, fftData, detections, status }}
 */
export default function useSignalWebSocket(url = WEBSOCKET_URL) {
  // ── Reactive state (drives re-renders) ──────────────────────────────────
  const [signalBuffer, setSignalBuffer] = useState([]);
  const [fftData,      setFftData]      = useState(null);
  const [detections,   setDetections]   = useState([]);
  const [status,       setStatus]       = useState('disconnected');

  // ── Refs (stable across renders, safe to read inside closures) ──────────
  const wsRef          = useRef(null);   // the live WebSocket instance
  const retryTimerRef  = useRef(null);   // setInterval handle for reconnect
  const unmountedRef   = useRef(false);  // guard: don't set state after unmount
  const urlRef         = useRef(url);    // keep URL in sync without re-running effect

  // Keep urlRef current if the caller passes a different url prop
  useEffect(() => { urlRef.current = url; }, [url]);

  // ── connect ─────────────────────────────────────────────────────────────
  const connect = useCallback(() => {
    // Bail out if we already have an open or connecting socket
    if (
      wsRef.current &&
      (wsRef.current.readyState === WebSocket.OPEN ||
       wsRef.current.readyState === WebSocket.CONNECTING)
    ) {
      return;
    }

    // Clear any pending retry timer before opening a new connection
    if (retryTimerRef.current) {
      clearTimeout(retryTimerRef.current);
      retryTimerRef.current = null;
    }

    let ws;
    try {
      ws = new WebSocket(urlRef.current);
    } catch (err) {
      // URL is malformed or environment blocks WS — schedule retry anyway
      console.warn('[EGO-WS] Failed to construct WebSocket:', err);
      scheduleReconnect();
      return;
    }

    wsRef.current = ws;

    // ── onopen ────────────────────────────────────────────────────────────
    ws.onopen = () => {
      if (unmountedRef.current) return;
      console.info('[EGO-WS] Connected to', urlRef.current);
      setStatus('connected');
    };

    // ── onmessage ─────────────────────────────────────────────────────────
    ws.onmessage = (event) => {
      if (unmountedRef.current) return;

      let data;
      try {
        data = JSON.parse(event.data);
      } catch {
        console.warn('[EGO-WS] Received non-JSON message, skipping.');
        return;
      }

      if (data.event === 'signal_data') {
        // ── Type 1: continuous raw signal + FFT ───────────────────────────
        const incoming = Array.isArray(data.samples) ? data.samples : [];

        setSignalBuffer(prev => {
          // Append new samples and keep only the last 500 data points.
          // Using a functional update avoids capturing stale `signalBuffer`
          // inside the closure.
          const combined = [...prev, ...incoming];
          return combined.length > 500
            ? combined.slice(combined.length - 500)
            : combined;
        });

        if (Array.isArray(data.fft_power) && Array.isArray(data.fft_freqs)) {
          setFftData({
            power: data.fft_power,
            freqs: data.fft_freqs,
          });
        }

      } else if (data.event === 'frequency_detected') {
        // ── Type 2: SSVEP detection event ────────────────────────────────
        const entry = {
          frequency:  data.frequency,
          confidence: typeof data.confidence === 'number'
            ? parseFloat(data.confidence.toFixed(3))
            : 0,
          mode:      data.mode  || 'unknown',
          timestamp: data.timestamp || new Date().toISOString(),
        };

        setDetections(prev => {
          // Newest first, cap at 50 entries
          const updated = [entry, ...prev];
          return updated.length > 50 ? updated.slice(0, 50) : updated;
        });

      } else {
        // Unknown event type — log and ignore so future message types don't break anything
        console.debug('[EGO-WS] Unknown event type:', data.event);
      }
    };

    // ── onerror ───────────────────────────────────────────────────────────
    ws.onerror = (err) => {
      // The browser fires onclose immediately after onerror,
      // so we handle reconnection there.
      console.warn('[EGO-WS] WebSocket error:', err);
    };

    // ── onclose ───────────────────────────────────────────────────────────
    ws.onclose = (event) => {
      if (unmountedRef.current) return;

      console.info(
        `[EGO-WS] Connection closed (code ${event.code}). Scheduling reconnect…`
      );
      setStatus('reconnecting');
      scheduleReconnect();
    };
  }, []); // no deps — reads everything via refs

  // ── scheduleReconnect ────────────────────────────────────────────────────
  function scheduleReconnect() {
    if (unmountedRef.current) return;
    if (retryTimerRef.current) return; // already scheduled

    retryTimerRef.current = setTimeout(() => {
      retryTimerRef.current = null;
      if (!unmountedRef.current) {
        setStatus('reconnecting');
        connect();
      }
    }, 2000);
  }

  // ── Lifecycle: mount / unmount ───────────────────────────────────────────
  useEffect(() => {
    unmountedRef.current = false;
    setStatus('reconnecting'); // immediately show "reconnecting" while we open
    connect();

    return () => {
      // Mark as unmounted FIRST so no state updates fire after teardown
      unmountedRef.current = true;

      // Cancel any pending reconnect timer
      if (retryTimerRef.current) {
        clearTimeout(retryTimerRef.current);
        retryTimerRef.current = null;
      }

      // Close the WebSocket cleanly — code 1000 = normal closure
      if (wsRef.current) {
        // Remove handlers before closing to prevent onclose firing the reconnect loop
        wsRef.current.onopen    = null;
        wsRef.current.onmessage = null;
        wsRef.current.onerror   = null;
        wsRef.current.onclose   = null;
        wsRef.current.close(1000, 'Component unmounted');
        wsRef.current = null;
      }
    };
  }, [connect]); // re-run only if `connect` identity changes (it won't — useCallback with no deps)

  // ── Public API ───────────────────────────────────────────────────────────
  return { signalBuffer, fftData, detections, status };
}
