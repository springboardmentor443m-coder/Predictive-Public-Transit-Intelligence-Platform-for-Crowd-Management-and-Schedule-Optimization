import { ArrowDownRight, ArrowUpRight, Minus, type LucideIcon } from "lucide-react";

type Accent = "brand" | "emerald" | "amber" | "rose" | "sky";
type Trend = "up" | "down" | "neutral";

interface KpiCardProps {
  label: string;
  value: React.ReactNode;
  change?: string;
  trend?: Trend;
  icon?: LucideIcon;
  accent?: Accent;
  sub?: string;
}

const accents: Record<Accent, string> = {
  brand: "bg-brand-500/15 text-brand-400 border-brand-500/30",
  emerald: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  amber: "bg-amber-500/15 text-amber-400 border-amber-500/30",
  rose: "bg-rose-500/15 text-rose-400 border-rose-500/30",
  sky: "bg-sky-500/15 text-sky-400 border-sky-500/30",
};

const glows: Record<Accent, string> = {
  brand: "hover:shadow-glow hover:border-brand-500/50",
  emerald: "hover:shadow-glow-emerald hover:border-emerald-500/50",
  amber: "hover:shadow-glow-amber hover:border-amber-500/50",
  rose: "hover:shadow-glow-rose hover:border-rose-500/50",
  sky: "hover:shadow-glow hover:border-sky-500/50",
};

export default function KpiCard({
  label,
  value,
  change,
  trend = "neutral",
  icon: Icon,
  accent = "brand",
  sub,
}: KpiCardProps) {
  const TrendIcon = trend === "up" ? ArrowUpRight : trend === "down" ? ArrowDownRight : Minus;
  const trendColor =
    trend === "up" ? "text-emerald-400" : trend === "down" ? "text-rose-400" : "text-slate-400";

  return (
    <div className={`card card-pad card-hover flex items-center gap-4 border-slate-800 ${glows[accent]}`}>
      {Icon && (
        <span className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl border ${accents[accent]}`}>
          <Icon className="h-6 w-6" />
        </span>
      )}
      <div className="min-w-0 flex-1">
        <p className="truncate text-[11px] font-extrabold uppercase tracking-[0.14em] text-slate-400">{label}</p>
        <div className="mt-1 flex items-baseline gap-2">
          <p className="text-3xl font-extrabold leading-none tracking-tight text-white font-mono">{value}</p>
          {change && (
            <span className={`inline-flex items-center gap-0.5 text-xs font-bold ${trendColor}`}>
              <TrendIcon className="h-3.5 w-3.5" />
              {change}
            </span>
          )}
        </div>
        {sub && <p className="mt-1.5 truncate text-[11px] font-medium text-slate-400">{sub}</p>}
      </div>
    </div>
  );
}