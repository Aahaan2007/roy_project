interface SSVEPCardProps {
  frequency: number;
  title: string;
  description: string;
  isActive: boolean;
}

export default function SSVEPCard({ frequency, title, description, isActive }: SSVEPCardProps) {
  return (
    <div
      className={`
        relative p-6 rounded-lg border-2 transition-all duration-300
        ${isActive
          ? 'border-cyan-400 bg-cyan-400/10 shadow-[0_0_20px_rgba(34,211,238,0.4)]'
          : 'border-gray-700 bg-gray-900/50'
        }
      `}
    >
      <div className="flex items-baseline gap-3 mb-2">
        <span className="font-mono text-3xl text-cyan-400">{frequency} Hz</span>
        <span className="text-gray-400">/</span>
        <span className="text-gray-300">{title}</span>
      </div>
      <p className="text-sm text-gray-400 font-mono">{description}</p>
      {isActive && (
        <div className="absolute top-2 right-2">
          <div className="w-3 h-3 bg-cyan-400 rounded-full animate-pulse"></div>
        </div>
      )}
    </div>
  );
}
