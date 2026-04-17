import { useEffect, useRef } from 'react';

interface EventLogProps {
  logs: { timestamp: string; message: string; level: string }[];
}

export default function EventLog({ logs }: EventLogProps) {
  const logContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs]);

  return (
    <div className="bg-gray-900/50 border-2 border-gray-700 rounded-lg p-6 h-full flex flex-col">
      <h3 className="font-mono text-lg mb-4 text-gray-300">
        ROY EVENT LOG
      </h3>
      <div
        ref={logContainerRef}
        className="flex-1 overflow-y-auto space-y-1 font-mono text-sm"
      >
        {logs.map((log, index) => (
          <div key={index} className="text-gray-400">
            <span className="text-cyan-400">[{log.timestamp}]</span>{' '}
            <span className={log.level === 'CRITICAL' ? 'text-orange-400' : 'text-gray-300'}>
              {log.level}:
            </span>{' '}
            {log.message}
          </div>
        ))}
      </div>
    </div>
  );
}
