import { AlertTriangle, BrainCircuit, Cpu, Database, Sparkles, TriangleAlert } from "lucide-react";
import type { ModelInfo, ModelSubInfo } from "../lib/types";

interface ModelBadgeProps {
  info: ModelInfo | null | undefined;
  compact?: boolean;
}

const CITY_LABELS: Record<string, string> = {
  seoul: "Seoul Metro",
  hangzhou: "Hangzhou Metro",
  nyc: "NYC Subway",
  tfl: "London TfL",
  beijing: "Beijing Metro",
};

type TaskKey = "crowd" | "demand";

const TASK_LABELS: Record<TaskKey, string> = {
  crowd: "Crowd",
  demand: "Demand",
};

/** Offline/degraded when the API says the artifact is missing OR that it failed at
 *  runtime. Both matter: an artifact that loads and then raises on every request
 *  is the more dangerous case, because `loaded` alone still reports `true` while
 *  the rule-based curve is answering.
 *
 *  `undefined`/`null` means the API omitted the field, which is not the same as
 *  "degraded" — we only claim degradation the backend actually reported. */
function isOffline(model: ModelSubInfo | undefined): boolean {
  return model?.loaded === false || model?.degraded === true;
}

function reasonFor(model: ModelSubInfo | undefined): string | null {
  return model?.degraded_reason ?? null;
}

function degradedTasks(info: ModelInfo): TaskKey[] {
  return (Object.keys(TASK_LABELS) as TaskKey[]).filter((k) => isOffline(info[k]));
}

export default function ModelBadge({ info, compact = false }: ModelBadgeProps) {
  if (!info) {
    return (
      <div
        role="status"
        aria-live="polite"
        className="flex items-center gap-2.5 rounded-2xl bg-slate-900 border border-slate-800 px-4 py-3 text-xs text-slate-400"
      >
        <BrainCircuit className="h-4 w-4 animate-spin text-brand-400" /> Loading active AI model parameters...
      </div>
    );
  }

  const cityLabel = CITY_LABELS[info.city] || info.city;
  // The NYC station map is empty because the app is keyed on native MTA stop ids
  // already, so the count is omitted rather than backfilled with a stale number.
  const mappedStations = Object.keys(info.station_map ?? {}).length;

  // Never fall back to invented numbers. A metric the API did not report is shown
  // as "n/a": a plausible-looking R² is indistinguishable from a measured one in
  // the UI, so hardcoding a default silently misrepresents the model.
  const fmt = (v: unknown, digits = 3) =>
    v == null || Number.isNaN(Number(v)) ? "n/a" : Number(v).toFixed(digits);

  const offline = degradedTasks(info);
  const degraded = offline.length > 0;
  const reasons = offline
    .map((k) => reasonFor(info[k]))
    .filter((r): r is string => typeof r === "string" && r.length > 0);
  // Delay is a separate, optional capability (different network entirely), so it
  // is reported but never counted as a degradation of the core pipeline.
  const algorithm = degraded
    ? "Rule-based baseline (no artifact)"
    : info.crowd?.algorithm || "XGBoost Machine Learning";

  const metrics: Array<[string, string, boolean]> = [
    ["Crowd R²", fmt(info.crowd?.metrics?.r2), isOffline(info.crowd)],
    ["Demand R²", fmt(info.demand?.metrics?.r2), isOffline(info.demand)],
    ["Crowd MAE", fmt(info.crowd?.metrics?.mae), isOffline(info.crowd)],
    ["Delay AUC", fmt(info.delay?.metrics?.auc), isOffline(info.delay)],
  ];

  return (
    <div
      role="status"
      aria-live="polite"
      data-testid="model-badge"
      data-serving-state={degraded ? "degraded" : "healthy"}
      className={`rounded-2xl border bg-slate-900/90 p-5 shadow-2xl backdrop-blur-xl ${
        degraded ? "border-amber-500/40" : "border-slate-800"
      }`}
    >
      <div className="flex items-center gap-3">
        <span
          className={`flex h-10 w-10 items-center justify-center rounded-2xl border shadow-lg ${
            degraded
              ? "bg-amber-500/10 border-amber-500/30 text-amber-400 shadow-amber-500/10"
              : "bg-brand-500/15 border-brand-500/30 text-brand-400 shadow-brand-500/10"
          }`}
        >
          {degraded ? <TriangleAlert className="h-5 w-5" /> : <BrainCircuit className="h-5 w-5" />}
        </span>
        <div>
          <div className="flex items-center gap-2">
            <p className="text-[10px] font-extrabold uppercase tracking-[0.16em] text-slate-400">
              {degraded ? "Degraded Serving Pipeline" : "Active Serving Pipeline"}
            </p>
            {!degraded && (
              <span className="inline-flex items-center gap-1 text-[10px] font-bold text-brand-400 bg-brand-500/10 border border-brand-500/20 px-2 py-0.5 rounded-full">
                <Sparkles className="h-3 w-3" /> Joblib Artifacts
              </span>
            )}
          </div>
          <p className="text-base font-extrabold text-white">
            {cityLabel} · {algorithm}
          </p>
        </div>
        <span
          className={`ml-auto inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-bold ${
            degraded
              ? "bg-amber-500/10 border-amber-500/30 text-amber-400"
              : "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
          }`}
        >
          {degraded ? (
            <>
              <AlertTriangle className="h-3 w-3" /> Fallback Active
            </>
          ) : (
            <>
              <span className="h-2 w-2 rounded-full bg-emerald-400 animate-ping" /> Live Serving
            </>
          )}
        </span>
      </div>

      {degraded && (
        <div
          data-testid="model-degraded-banner"
          className="mt-4 flex items-start gap-2.5 rounded-xl border border-amber-500/30 bg-amber-500/10 px-3.5 py-3 text-xs text-amber-200"
        >
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-400" />
          <p>
            <span className="font-bold text-amber-300">
              {offline.map((k) => TASK_LABELS[k]).join(" and ")} model
              {offline.length > 1 ? "s are" : " is"} not serving.
            </span>{" "}
            Predictions are being served by the rule-based baseline curve, not a trained model. Metrics shown
            below describe the artifact on disk and do not describe the values currently being returned.
            {reasons.length > 0 && (
              <span className="mt-1 block font-mono text-[11px] text-amber-300/70">{reasons.join(" · ")}</span>
            )}
          </p>
        </div>
      )}

      <div className="mt-4 grid grid-cols-2 gap-2.5 sm:grid-cols-4">
        {metrics.map(([k, v, offlineMetric]) => (
          <div
            key={k}
            className={`rounded-xl border p-2.5 text-center ${
              offlineMetric ? "border-amber-500/25 bg-amber-500/5" : "border-slate-800/80 bg-slate-950/60"
            }`}
          >
            <p className="text-[10px] font-extrabold uppercase tracking-wider text-slate-400">{k}</p>
            <p
              className={`text-sm font-extrabold font-mono mt-0.5 ${
                offlineMetric ? "text-amber-300/80 line-through decoration-amber-500/40" : "text-white"
              }`}
            >
              {offlineMetric ? "offline" : v}
            </p>
          </div>
        ))}
      </div>

      {!compact && (
        <div className="mt-3.5 flex flex-wrap items-center justify-between border-t border-slate-800/80 pt-3 text-xs text-slate-400 gap-2">
          <span className="flex items-center gap-1.5">
            <Database className="h-3.5 w-3.5 text-brand-400" />
            {info.datasets?.[info.city] || "Smart-card ridership logs"}
            {mappedStations > 0 && ` · ${mappedStations} mapped stations`}
          </span>
          <span className="flex items-center gap-1 font-mono text-[11px] text-slate-400">
            <Cpu className={`h-3.5 w-3.5 ${degraded ? "text-amber-400" : "text-emerald-400"}`} />
            {degraded ? "Baseline latency" : "Latency < 15ms inference"}
          </span>
        </div>
      )}
    </div>
  );
}
