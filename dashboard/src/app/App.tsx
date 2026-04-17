import { useState, useEffect } from 'react';
import SSVEPCard from './components/SSVEPCard';
import EEGWaveform from './components/EEGWaveform';
import FFTSpectrum from './components/FFTSpectrum';
import EventLog from './components/EventLog';

interface LogEntry {
  timestamp: string;
  message: string;
  level: string;
}

export default function App() {
  const [activeFrequency, setActiveFrequency] = useState<number | null>(null);
  const [waveformData, setWaveformData] = useState<number[]>([]);
  const [fftData, setFftData] = useState<{ frequency: number; power: number }[]>([]);
  const [logs, setLogs] = useState<LogEntry[]>([
    { timestamp: '22:00:00', message: 'System initialized. Awaiting neural link...', level: 'INFO' },
    { timestamp: '22:00:15', message: 'WebSocket connection established.', level: 'INFO' },
  ]);

  const addLog = (message: string, level: string = 'INFO') => {
    const now = new Date();
    const timestamp = now.toTimeString().split(' ')[0];
    setLogs((prev) => [...prev, { timestamp, message, level }]);
  };

  useEffect(() => {
    const wsUrl = 'ws://localhost:8766';
    let ws: WebSocket | null = null;
    let reconnectTimer: number | null = null;

    const connect = () => {
      try {
        ws = new WebSocket(wsUrl);

        ws.onopen = () => {
          addLog('Neural link established with Signal Server (PC1/PC2).', 'INFO');
          // Register as dashboard so we get signal data
          ws?.send(JSON.stringify({ type: 'register', role: 'dashboard' }));
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);

            if (data.type === 'signal_data') {
              setWaveformData(data.amplitude);
              setActiveFrequency(data.active_freq);
            } else if (data.type === 'fft_data') {
              const formattedFFT = data.frequencies.map((freq: number, i: number) => ({
                frequency: Math.round(freq),
                power: data.magnitudes[i],
              }));
              // Only show up to 40Hz to match typical SSVEP ranges
              setFftData(formattedFFT.filter((f: any) => f.frequency <= 40));
            } else if (data.type === 'freq_detected') {
              addLog(`[DETECTED] ${data.frequency}Hz SSVEP -> ${data.label}`, 'CRITICAL');
              setActiveFrequency(data.frequency);
            } else if (data.type === 'roy_response') {
              addLog(`[ROY] ${data.response}`, 'INFO');
              // Clear active frequency highlighting after a few seconds
              setTimeout(() => {
                setActiveFrequency(null);
                setWaveformData([]);
              }, 4000);
            }
          } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
          }
        };

        ws.onerror = () => {
          addLog('WebSocket connection error. Retrying...', 'WARNING');
        };

        ws.onclose = () => {
          addLog('Neural link severed. reconnecting...', 'WARNING');
          reconnectTimer = window.setTimeout(connect, 3000);
        };
      } catch (error) {
        addLog('WebSocket unavailable. Retrying in 5s...', 'WARNING');
        reconnectTimer = window.setTimeout(connect, 5000);
      }
    };

    connect();

    return () => {
      if (ws) ws.close();
      if (reconnectTimer) clearTimeout(reconnectTimer);
    };
  }, []);

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-gray-100 font-mono p-8">
      <header className="flex justify-between items-center mb-8 pb-4 border-b-2 border-gray-700">
        <div>
          <h1 className="text-3xl text-cyan-400">Project E.G.O.</h1>
          <p className="text-sm text-gray-400">NEURAL DASHBOARD v1.0</p>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-gray-300">Aahan A.</span>
          <div className="flex items-center gap-2 px-4 py-2 bg-green-900/30 border border-green-600 rounded">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
            <span className="text-green-400 text-sm">STATUS: Linked</span>
          </div>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <EEGWaveform data={waveformData} />
          <FFTSpectrum data={fftData} activeFrequency={activeFrequency} />
        </div>

        <div className="space-y-4">
          <SSVEPCard
            frequency={7}
            title="Open Notepad"
            description="APP_LAUNCH"
            isActive={activeFrequency === 7}
          />
          <SSVEPCard
            frequency={10}
            title="Google Search"
            description="WEB_SEARCH"
            isActive={activeFrequency === 10}
          />
          <SSVEPCard
            frequency={12}
            title="Play on YouTube"
            description="MEDIA_PLAY"
            isActive={activeFrequency === 12}
          />
          <SSVEPCard
            frequency={15}
            title="Take Screenshot"
            description="SCREENSHOT"
            isActive={activeFrequency === 15}
          />
          <SSVEPCard
            frequency={20}
            title="System Status"
            description="SYS_INFO"
            isActive={activeFrequency === 20}
          />
        </div>
      </div>

      <div className="mt-6 h-64">
        <EventLog logs={logs} />
      </div>
    </div>
  );
}
