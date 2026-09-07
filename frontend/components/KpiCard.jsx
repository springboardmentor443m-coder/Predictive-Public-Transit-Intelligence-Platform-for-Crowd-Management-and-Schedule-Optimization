import { ArrowDownRight, ArrowUpRight, Minus } from "lucide-react";

export default function KpiCard({ label, value, change, trend = "neutral", icon: Icon, accent = "brand" }) {
  const accents = {
    brand: "bg-brand-50 text-brand-600",
    emerald: "bg-emerald-50 text-emerald-600",
    amber: "bg-amber-50 text-amber-600",
    rose: "bg-rose-50 text-rose-600",
    sky: "bg-sky-50 text-sky-600",
  };
  const TrendIcon = trend === "up" ? ArrowUpRight : trend === "down" ? ArrowDownRight : Minus;
  const trendColor =
    trend === "up" ? "text-emerald-600" : trend === "down" ? "text-rose-600" : "text-slate-400";

  return (
    <div className="card card-pad flex items-center gap-4">
      {Icon && (
        <span className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl ${accents[accent] || accents.brand}`}>
          <Icon className="h-5 w-5" />
        </span>
      )}
      <div className="min-w-0">
        <p className="truncate text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
        <div className="mt-0.5 flex items-baseline gap-2">
          <p className="text-2xl font-bold leading-none text-slate-900">{value}</p>
          {change && (
            <span className={`inline-flex items-center gap-0.5 text-xs font-semibold ${trendColor}`}>
              <TrendIcon className="h-3.5 w-3.5" />
              {change}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
