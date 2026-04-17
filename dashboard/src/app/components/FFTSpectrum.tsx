import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Cell } from 'recharts';

interface FFTSpectrumProps {
  data: { frequency: number; power: number }[];
  activeFrequency: number | null;
}

export default function FFTSpectrum({ data, activeFrequency }: FFTSpectrumProps) {
  return (
    <div className="bg-gray-900/50 border-2 border-gray-700 rounded-lg p-6">
      <h3 className="font-mono text-lg mb-4 text-gray-300">
        FFT FREQUENCY SPECTRUM
      </h3>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={data}>
          <XAxis
            dataKey="frequency"
            stroke="#6b7280"
            style={{ fontSize: '12px', fontFamily: 'monospace' }}
          />
          <YAxis
            stroke="#6b7280"
            style={{ fontSize: '12px', fontFamily: 'monospace' }}
            label={{ value: 'Power', angle: -90, position: 'insideLeft', fill: '#6b7280' }}
          />
          <Bar dataKey="power" radius={[4, 4, 0, 0]}>
            {data.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={entry.frequency === activeFrequency ? '#22d3ee' : '#fb923c'}
                opacity={entry.frequency === activeFrequency ? 1 : 0.3}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
