import { useEffect, useRef } from 'react';

interface EEGWaveformProps {
  data: number[];
}

export default function EEGWaveform({ data }: EEGWaveformProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;

    ctx.fillStyle = '#0a0a0a';
    ctx.fillRect(0, 0, width, height);

    ctx.strokeStyle = '#22d3ee';
    ctx.lineWidth = 2;
    ctx.beginPath();

    const step = width / data.length;
    const amplitude = height / 2;

    data.forEach((value, index) => {
      const x = index * step;
      const y = amplitude - value * amplitude * 0.8;

      if (index === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    });

    ctx.stroke();

    ctx.strokeStyle = '#1f2937';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, amplitude);
    ctx.lineTo(width, amplitude);
    ctx.stroke();
  }, [data]);

  return (
    <div className="bg-gray-900/50 border-2 border-gray-700 rounded-lg p-6">
      <h3 className="font-mono text-lg mb-4 text-gray-300">
        LIVE EEG WAVEFORM
      </h3>
      <canvas
        ref={canvasRef}
        width={800}
        height={200}
        className="w-full h-auto"
      />
    </div>
  );
}
