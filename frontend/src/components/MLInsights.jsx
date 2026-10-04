import React, { useEffect, useState } from 'react';
import { Brain, Target, TrendingUp, BarChart3, Info, Cpu } from 'lucide-react';
import { fetchMLMetrics } from '../services/api';
import ErrorHeatmap from './ErrorHeatmap';

function MetricCard({ label, value, sub, tone = 'cyan' }) {
  const tones = {
    cyan: 'border-cyan-500/20 text-cyan-300',
    emerald: 'border-emerald-500/20 text-emerald-300',
    amber: 'border-amber-500/20 text-amber-300',
    slate: 'border-slate-700 text-slate-300',
  };
  return (
    <div className={`rounded-xl border bg-slate-900/60 p-3.5 ${tones[tone]}`}>
      <p className="text-[10px] font-semibold uppercase tracking-wider opacity-70">
        {label}
      </p>
      <p className="text-xl font-black font-display tabular-nums leading-tight">
        {value}
      </p>
      {sub && <p className="text-[10px] font-mono opacity-60">{sub}</p>}
    </div>
  );
}

function ModelBlock({ title, model, tone }) {
  // available===false is the explicit "not evaluable" signal from the backend
  if (!model) return null;
  if (model.available === false) {
    return (
      <div className="glass-panel rounded-2xl border border-slate-800 p-5">
        <h3 className="text-sm font-bold text-slate-300">{title}</h3>
        <p className="text-[11px] text-slate-500 font-mono mt-1">
          {model.reason || 'not available'}
        </p>
      </div>
    );
  }

  // peak vs off-peak mean error, so the hourly chart reads at a glance.
  // Computed here because this is the scope that actually has the data.
  const byHour = model.by_hour || [];
  const maxMae = byHour.length ? Math.max(...byHour.map((h) => h.mae)) || 1 : 1;
  const meanOf = (arr) =>
    arr.length ? (arr.reduce((s, x) => s + x.mae, 0) / arr.length).toFixed(0) : '—';
  const peakMae = meanOf(byHour.filter((h) => h.hour >= 8 && h.hour <= 11));
  const offPeakMae = meanOf(byHour.filter((h) => !(h.hour >= 8 && h.hour <= 11)));

  return (
    <div className="glass-panel rounded-2xl border border-slate-800 p-5">
      <div className="flex items-center gap-2 mb-4">
        <div
          className={`p-2 rounded-lg border ${
            tone === 'emerald'
              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
              : 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20'
          }`}
        >
          <Cpu className="w-4 h-4" />
        </div>
        <div>
          <h3 className="text-sm font-bold text-white">{title}</h3>
          <p className="text-[10px] text-slate-500 font-mono">
            target: {model.target}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <MetricCard
          label="R² score"
          value={model.r2}
          sub="variance explained"
          tone={tone}
        />
        <MetricCard label="MAE" value={model.mae} sub="passengers" tone="slate" />
        <MetricCard label="RMSE" value={model.rmse} sub="passengers" tone="slate" />
        <MetricCard
          label="MAPE"
          value={`${model.mape}%`}
          sub={`${model.within_10pct}% within ±10%`}
          tone="amber"
        />
      </div>

      <div className="mt-3 grid grid-cols-2 lg:grid-cols-4 gap-3">
        <MetricCard label="Train rows" value={model.rows_train} tone="slate" />
        <MetricCard label="Test rows" value={model.rows_test} tone="slate" />
        <MetricCard label="Bias" value={model.bias} sub="mean signed error" tone="slate" />
        <MetricCard
          label="Split"
          value="80/20"
          sub="chronological"
          tone="slate"
        />
      </div>

      {model.feature_importance?.length > 0 && (
        <div className="mt-4 pt-4 border-t border-slate-800/70">
          <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-2.5 flex items-center gap-1.5">
            <BarChart3 className="w-3 h-3" /> Feature importance (gain)
          </p>
          <div className="space-y-1.5">
            {model.feature_importance.slice(0, 6).map((f) => {
              const max = model.feature_importance[0].importance || 1;
              return (
                <div key={f.feature} className="flex items-center gap-2">
                  <span className="text-[10px] font-mono text-slate-400 w-32 shrink-0 truncate">
                    {f.feature}
                  </span>
                  <div className="flex-1 h-2 bg-slate-800 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        tone === 'emerald'
                          ? 'bg-gradient-to-r from-emerald-500 to-teal-400'
                          : 'bg-gradient-to-r from-cyan-500 to-blue-400'
                      }`}
                      style={{ width: `${(f.importance / max) * 100}%` }}
                    />
                  </div>
                  <span className="text-[10px] font-mono text-slate-300 w-12 text-right tabular-nums">
                    {(f.importance * 100).toFixed(1)}%
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {model.by_hour?.length > 0 && (
        <div className="mt-4 pt-4 border-t border-slate-800/70">
          <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-2.5">
            Error by hour of day — MAE
          </p>
          {/* h-full on each column is required: the bar's percentage height
              resolves against this element, and without an explicit height it
              collapses to zero and renders nothing. */}
          <div className="flex items-end gap-1 h-24">
            {model.by_hour.map((h) => {
              const isPeak = h.hour >= 8 && h.hour <= 11;
              return (
                <div
                  key={h.hour}
                  className="flex-1 h-full flex flex-col items-center justify-end group relative"
                  title={`${String(h.hour).padStart(2, '0')}:00 — actual ${h.mean_actual}, predicted ${h.mean_predicted}, MAE ${h.mae}, bias ${h.bias}`}
                >
                  <span className="text-[8px] font-mono text-slate-500 mb-0.5 tabular-nums opacity-0 group-hover:opacity-100 transition-opacity">
                    {h.mae.toFixed(0)}
                  </span>
                  <div
                    className={`w-full rounded-t transition-all min-h-[2px] ${
                      isPeak
                        ? 'bg-amber-500/80 group-hover:bg-amber-400'
                        : 'bg-cyan-600/70 group-hover:bg-cyan-400'
                    }`}
                    style={{ height: `${(h.mae / maxMae) * 100}%` }}
                  />
                </div>
              );
            })}
          </div>
          <div className="flex gap-1 mt-1">
            {model.by_hour.map((h) => (
              <span
                key={h.hour}
                className={`flex-1 text-center text-[8px] font-mono ${
                  h.hour >= 8 && h.hour <= 11 ? 'text-amber-500/70' : 'text-slate-600'
                }`}
              >
                {h.hour}
              </span>
            ))}
          </div>
          <div className="flex items-center gap-3 mt-2 text-[9px] font-mono text-slate-500 flex-wrap">
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-sm bg-amber-500/80" /> peak hours
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-sm bg-cyan-600/70" /> off-peak
            </span>
            <span>bar height = MAE (passengers)</span>
            <span>· peak mean {peakMae} · off-peak mean {offPeakMae}</span>
          </div>
        </div>
      )}

      {model.heatmap?.rows?.length > 0 && (
        <div className="mt-4 pt-4 border-t border-slate-800/70">
          <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-2.5">
            Error Heatmap — station × hour
          </p>
          <ErrorHeatmap heatmap={model.heatmap} />
        </div>
      )}

      {model.by_station?.length > 0 && (
        <div className="mt-4 pt-4 border-t border-slate-800/70">
          <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
            Error by station
          </p>
          <div className="grid grid-cols-2 lg:grid-cols-5 gap-2">
            {[...model.by_station]
              .sort((a, b) => b.mae - a.mae)
              .map((s) => (
                <div
                  key={s.station}
                  className="rounded-lg bg-slate-900/70 border border-slate-800 p-2"
                >
                  <p className="text-[10px] text-slate-300 truncate">{s.station}</p>
                  <p className="text-sm font-bold text-cyan-300 font-display tabular-nums">
                    {s.mae}
                  </p>
                  <p className="text-[9px] font-mono text-slate-500">
                    bias {s.bias}
                  </p>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default function MLInsights() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchMLMetrics()
      .then(setData)
      .catch((err) => setError(err.message));
  }, []);

  if (error) {
    return (
      <div className="glass-panel rounded-2xl border border-red-500/30 p-8 text-center">
        <p className="text-sm text-red-300 font-mono">ML metrics unavailable: {error}</p>
      </div>
    );
  }
  if (!data) {
    return (
      <div className="glass-panel rounded-2xl border border-slate-800 p-12 text-center">
        <Brain className="w-10 h-10 text-cyan-400 mx-auto mb-3 animate-pulse" />
        <p className="text-sm text-slate-400 font-mono">
          Evaluating models on hold-out split…
        </p>
      </div>
    );
  }

  // Guard the shape we depend on. Without this a malformed or partial response
  // throws during render, and because this is a top-level tab the whole app
  // unmounts and the user just sees a blank page.
  if (!data.occupancy_model) {
    return (
      <div className="glass-panel rounded-2xl border border-amber-500/30 p-8 text-center">
        <p className="text-sm text-amber-300 font-mono">
          The metrics response did not include an occupancy model.
        </p>
        <p className="text-[11px] text-slate-500 font-mono mt-2">
          Check that the backend is running and /api/ml/metrics returns 200.
        </p>
      </div>
    );
  }

  const om = data.occupancy_model;
  const cm = data.crowd_model;

  return (
    <div className="space-y-6">
      {/* headline */}
      <div className="glass-panel rounded-2xl border border-slate-800 p-5">
        <div className="flex items-start gap-3">
          <div className="p-2.5 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 shrink-0">
            <Brain className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white">Model Evaluation</h2>
            <p className="text-xs text-slate-400 mt-1">
              Two gradient-boosted regressors run side by side. Both are scored on
              the final 20% of the dataset taken in time order — the split is never
              shuffled, so no future information leaks into training.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mt-5">
          <MetricCard
            label="Dataset"
            value={(om.rows_total ?? 0).toLocaleString()}
            sub="trips, Jan–Dec 2023"
            tone="slate"
          />
          <MetricCard
            label="Features"
            value={data.features.length}
            sub="cyclical + categorical"
            tone="slate"
          />
          <MetricCard
            label="Best R²"
            value={Math.max(om.r2 ?? 0, cm?.r2 ?? 0)}
            sub="occupancy regressor"
            tone="emerald"
          />
          <MetricCard
            label="Hardest station"
            value={om.hardest_station || '—'}
            sub="highest MAE"
            tone="amber"
          />
        </div>
      </div>

      <ModelBlock title="Occupancy Model (shipped)" model={om} tone="cyan" />
      <ModelBlock title="Platform Crowd Model (live dashboard)" model={cm} tone="emerald" />

      {/* methodology */}
      <div className="glass-panel rounded-2xl border border-slate-800 p-5">
        <h3 className="text-sm font-bold text-white flex items-center gap-2 mb-3">
          <Info className="w-4 h-4 text-amber-400" />
          Methodology
        </h3>
        <ul className="space-y-2 text-[11px] text-slate-400 leading-relaxed">
          <li className="flex gap-2">
            <Target className="w-3.5 h-3.5 text-cyan-400 shrink-0 mt-0.5" />
            <span>
              <strong className="text-slate-300">Two targets, two models.</strong> The
              shipped model predicts passengers <em>on board</em>; the dashboard also
              needs a forecast of passengers <em>waiting</em>, so a second regressor
              is trained on platform crowd density. Comparing one against the other
              would be meaningless — each live figure is compared to a forecast of
              the same quantity.
            </span>
          </li>
          <li className="flex gap-2">
            <TrendingUp className="w-3.5 h-3.5 text-cyan-400 shrink-0 mt-0.5" />
            <span>
              <strong className="text-slate-300">Feature engineering.</strong> Hour of
              day is encoded both raw and cyclically (sin/cos) so that 23:00 and 00:00
              sit adjacent rather than at opposite ends of the scale. Peak-hour
              membership and label-encoded station/line/day complete the nine
              features.
            </span>
          </li>
          <li className="flex gap-2">
            <Brain className="w-3.5 h-3.5 text-cyan-400 shrink-0 mt-0.5" />
            <span>
              <strong className="text-slate-300">What the model learned.</strong> Peak
              hour dominates the gain in both models, which matches the data: crowd
              is strongly bimodal across the day (≈100 waiting off-peak versus ≈950 at
              the evening peak). Midday hours carry the largest error, since demand is
              both elevated and volatile there.
            </span>
          </li>
          <li className="flex gap-2">
            <Cpu className="w-3.5 h-3.5 text-cyan-400 shrink-0 mt-0.5" />
            <span>
              <strong className="text-slate-300">Serving path.</strong> Predictions are
              produced by the same boosters the dashboard calls — loaded from native
              XGBoost JSON, never re-implemented in Python.
            </span>
          </li>
        </ul>
      </div>
    </div>
  );
}