import { AlertTriangle, ArrowRight, Lightbulb, TrendingUp } from "lucide-react";
import StatusBadge from "./StatusBadge";
import type {
  AiInsights,
  InsightAction,
  InsightDemandOutlook,
  InsightStation,
} from "../lib/types";

interface InsightPanelProps {
  insights: AiInsights | null | undefined;
  onSelectStation?: (stationId: string) => void;
}

const statusStyleMap: Record<string, string> = {
  healthy: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
  watch: "bg-amber-500/15 text-amber-300 border-amber-500/30",
  strained: "bg-rose-500/20 text-rose-300 border-rose-500/40 animate-pulse",
};

export default function InsightPanel({ insights, onSelectStation }: InsightPanelProps) {
  if (!insights) {
    return (
      <div className="card card-pad text-sm text-slate-400 flex items-center justify-center py-8">
        <Lightbulb className="mr-2 h-4 w-4 animate-bounce text-amber-400" /> Generating AI operational insights...
      </div>
    );
  }

  const statusStyle =
    statusStyleMap[insights.network_status] || "bg-slate-800 text-slate-300 border-slate-700";

  const topActions: InsightAction[] = insights.top_actions || [];
  const criticalStations: InsightStation[] = insights.critical_stations || [];
  const demandOutlook: InsightDemandOutlook[] = insights.demand_outlook || [];

  return (
    <div className="card overflow-hidden border-slate-800">
      <div className="flex flex-wrap items-center gap-3 border-b border-slate-800 bg-gradient-to-r from-brand-950/40 via-slate-900/60 to-transparent px-5 py-4">
        <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-amber-500/15 border border-amber-500/30 text-amber-400 shadow-lg shadow-amber-500/10">
          <Lightbulb className="h-5 w-5" />
        </span>
        <div>
          <h3 className="font-extrabold tracking-tight text-white">AI Operational Insights & Dispatch Suggestions</h3>
          <p className="text-xs text-slate-400">
            Peak forecast: <span className="font-bold text-white">{String(insights.predicted_peak_hour ?? "--").padStart(2, "0")}:00</span> · {insights.recommendations_count ?? 0} recommendations · {insights.open_alerts ?? 0} active alerts
          </p>
        </div>
        <span className={`ml-auto inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-extrabold uppercase tracking-wide border ${statusStyle}`}>
          {insights.network_status}
        </span>
      </div>

      <div className="grid grid-cols-1 gap-0 md:grid-cols-2 divide-y divide-slate-800/80 md:divide-y-0 md:divide-x">
        {/* Left Column: Top Recommended Actions */}
        <div className="p-5 space-y-3">
          <p className="section-title">Top Recommended Dispatch Actions</p>
          {topActions.length === 0 ? (
            <p className="text-xs text-slate-500 py-4">All stations within target capacity. No emergency dispatch required.</p>
          ) : (
            <ul className="space-y-2.5">
              {topActions.map((a) => (
                <li key={a.station_id || a.station_name} className="flex items-start gap-3 rounded-xl bg-slate-950/60 p-3 border border-slate-800/80 hover:border-slate-700 transition">
                  <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-400" />
                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-extrabold text-white">{a.station_name}</p>
                    <p className="text-[11px] text-slate-400 mt-0.5">{a.action} · {a.reason}</p>
                  </div>
                  {onSelectStation && a.station_id && (
                    <button
                      onClick={() => onSelectStation(a.station_id!)}
                      className="inline-flex shrink-0 items-center gap-1 text-xs font-extrabold text-brand-400 hover:text-brand-300 transition"
                    >
                      View <ArrowRight className="h-3.5 w-3.5" />
                    </button>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Right Column: Critical Stations & Demand Outlook */}
        <div className="p-5 space-y-4">
          <div>
            <p className="section-title mb-2.5">Strained Stations Monitor</p>
            {criticalStations.length === 0 ? (
              <p className="text-xs text-slate-500">No high/critical congestion across network.</p>
            ) : (
              <ul className="space-y-2.5">
                {criticalStations.slice(0, 4).map((s) => (
                  <li key={s.station_id} className="flex items-center gap-3">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-baseline justify-between gap-2">
                        <p className="truncate text-xs font-extrabold text-white">{s.station_name}</p>
                        <p className="text-xs font-mono font-extrabold text-slate-300">{s.occupancy_pct}%</p>
                      </div>
                      <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-slate-800">
                        <div
                          className="h-full rounded-full bg-gradient-to-r from-amber-400 to-rose-500 transition-all duration-500"
                          style={{ width: `${Math.min(100, s.occupancy_pct)}%` }}
                        />
                      </div>
                    </div>
                    <StatusBadge value={s.congestion_level} />
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Demand Outlook */}
          {demandOutlook.length > 0 && (
            <div className="rounded-xl bg-brand-950/40 p-3.5 border border-brand-800/40">
              <p className="flex items-center gap-1.5 text-[10px] font-extrabold uppercase tracking-wider text-brand-400 mb-1.5">
                <TrendingUp className="h-3.5 w-3.5" /> 3-Hour Passenger Inflow Outlook
              </p>
              <div className="space-y-1">
                {demandOutlook.slice(0, 3).map((d) => (
                  <p key={d.station_id || d.station_name} className="text-xs text-slate-300">
                    <span className="font-bold text-white">{d.station_name}:</span>{" "}
                    <span className="font-mono text-brand-300">
                      {(d.next_3h_entries || []).map((v) => Number(v).toLocaleString()).join(" → ")} pax
                    </span>
                  </p>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}