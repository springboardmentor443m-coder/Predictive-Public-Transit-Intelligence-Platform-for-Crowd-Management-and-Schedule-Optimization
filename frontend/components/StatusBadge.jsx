const STYLES = {
  low: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
  medium: "bg-amber-500/15 text-amber-300 border-amber-500/30",
  high: "bg-orange-500/15 text-orange-300 border-orange-500/30",
  critical: "bg-rose-500/20 text-rose-300 border-rose-500/40 animate-pulse",
  on_time: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
  delayed: "bg-amber-500/15 text-amber-300 border-amber-500/30",
  cancelled: "bg-rose-500/20 text-rose-300 border-rose-500/40",
  overcrowding: "bg-rose-500/20 text-rose-300 border-rose-500/40",
  delay: "bg-amber-500/15 text-amber-300 border-amber-500/30",
  emergency: "bg-rose-600/30 text-rose-200 border-rose-500/60 font-extrabold animate-pulse",
  info: "bg-sky-500/15 text-sky-300 border-sky-500/30",
  admin: "bg-indigo-500/20 text-indigo-300 border-indigo-500/30",
  operator: "bg-brand-500/20 text-brand-300 border-brand-500/30",
  viewer: "bg-slate-500/20 text-slate-300 border-slate-500/30",
};

const LABELS = {
  on_time: "On time",
};

export default function StatusBadge({ value }) {
  const key = String(value || "").toLowerCase();
  const style = STYLES[key] || "bg-slate-800 text-slate-300 border-slate-700";
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold capitalize border backdrop-blur-sm ${style}`}>
      {LABELS[key] || value}
    </span>
  );
}

export function congestionColor(pct) {
  if (pct >= 90) return "#f43f5e"; // rose-500
  if (pct >= 75) return "#f97316"; // orange-500
  if (pct >= 55) return "#eab308"; // yellow-500
  return "#10b981"; // emerald-500
}
