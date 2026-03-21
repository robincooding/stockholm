const REGIME_CONFIG = {
  bull:       { label: "강한 상승장", color: "bg-bull/20 text-bull border-bull/50" },
  weak_bull:  { label: "약한 상승장", color: "bg-green-800/20 text-green-400 border-green-600/50" },
  bear:       { label: "강한 하락장", color: "bg-bear/20 text-bear border-bear/50" },
  weak_bear:  { label: "약한 하락장", color: "bg-red-800/20 text-red-400 border-red-600/50" },
  range:      { label: "횡보장",     color: "bg-yellow-800/20 text-yellow-400 border-yellow-600/50" },
};

export default function RegimeBadge({ regime }) {
  const config = REGIME_CONFIG[regime] || REGIME_CONFIG["range"];
  return (
    <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border ${config.color}`}>
      {config.label}
    </span>
  );
}