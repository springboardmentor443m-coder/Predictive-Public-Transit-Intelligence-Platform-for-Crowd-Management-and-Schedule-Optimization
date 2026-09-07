const STYLES = {
  low: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  medium: "bg-amber-50 text-amber-700 ring-amber-200",
  high: "bg-orange-50 text-orange-700 ring-orange-200",
  critical: "bg-rose-50 text-rose-700 ring-rose-200",
  on_time: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  delayed: "bg-amber-50 text-amber-700 ring-amber-200",
  cancelled: "bg-rose-50 text-rose-700 ring-rose-200",
  overcrowding: "bg-rose-50 text-rose-700 ring-rose-200",
  delay: "bg-amber-50 text-amber-700 ring-amber-200",
  emergency: "bg-rose-100 text-rose-800 ring-rose-300",
  info: "bg-sky-50 text-sky-700 ring-sky-200",
};

const LABELS = {
  on_time: "On time",
};

export default function StatusBadge({ value }) {
  const key = String(value || "").toLowerCase();
  const style = STYLES[key] || "bg-slate-100 text-slate-600 ring-slate-200";
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold capitalize ring-1 ${style}`}>
      {LABELS[key] || value}
    </span>
  );
}

export function congestionColor(pct) {
  if (pct >= 90) return "#e11d48";
  if (pct >= 75) return "#f97316";
  if (pct >= 55) return "#f59e0b";
  return "#10b981";
}
