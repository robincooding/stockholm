export default function StatCard({ label, value, unit = "", color = "text-white" }) {
  return (
    <div className="bg-cardbg border border-border rounded-xl p-4 flex flex-col gap-1">
      <span className="text-neutral text-xs">{label}</span>
      <span className={`text-2xl font-bold ${color}`}>
        {value}
        {unit && <span className="text-sm font-normal ml-1">{unit}</span>}
      </span>
    </div>
  );
}