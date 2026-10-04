import React from 'react';
import { Users, TrendingUp, TrendingDown, Minus, Train, AlertTriangle } from 'lucide-react';

/**
 * One station's live crowd reading next to the ML forecast for the same moment.
 *
 * The two bars are drawn on a shared scale so the gap is immediately readable:
 * a red gap means passengers are stranded on the platform beyond plan.
 */
export default function StationCrowdCard({ station, thresholdPct = 20 }) {
  const {
    station: name,
    live_platform_crowd: live,
    predicted_crowd: pred,
    deviation_pct: dev,
    tier,
    capacity,
    actual_train_occupancy: occ,
    predicted_occupancy: predOcc,
    is_anomaly: anomaly,
    delay_pressure: pressure,
    lines,
    next_trains: nextTrains,
  } = station;

  // shared scale so the bars are directly comparable
  const scaleMax = Math.max(live, pred, 1) * 1.15;
  const liveW = (live / scaleMax) * 100;
  const predW = (pred / scaleMax) * 100;

  const tierStyle = {
    SEVERE_RUSH: 'bg-red-500/15 text-red-300 border-red-500/30',
    MODERATE_TRAFFIC: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
    OFF_PEAK: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
  }[tier] || 'bg-slate-700/30 text-slate-300 border-slate-600/30';

  const DevIcon = dev > 5 ? TrendingUp : dev < -5 ? TrendingDown : Minus;
  const devColor = anomaly ? 'text-red-400' : dev > 5 ? 'text-amber-400' : 'text-slate-400';

  return (
    <div
      className={`glass-panel rounded-2xl border p-5 transition-all duration-300 relative overflow-hidden ${
        anomaly
          ? 'border-red-500/50 shadow-lg shadow-red-500/10'
          : 'border-slate-800 hover:border-slate-700'
      }`}
    >
      {anomaly && (
        <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-red-500 via-orange-500 to-red-500" />
      )}

      {/* header */}
      <div className="flex items-start justify-between gap-2 mb-4">
        <div className="min-w-0">
          <h3 className="text-sm font-bold text-white truncate">{name}</h3>
          <p className="text-[10px] text-slate-500 font-mono truncate mt-0.5">
            {lines.join(' · ')}
          </p>
        </div>
        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md border shrink-0 font-mono ${tierStyle}`}>
          {tier.replace('_', ' ')}
        </span>
      </div>

      {/* live headline */}
      <div className="flex items-end justify-between mb-1">
        <div>
          <span className="text-3xl font-black text-white font-display tabular-nums">
            {live.toLocaleString()}
          </span>
          <span className="text-[11px] text-slate-500 ml-1.5">on platform</span>
        </div>
        <div className={`flex items-center gap-1 text-xs font-mono font-semibold ${devColor}`}>
          <DevIcon className="w-3.5 h-3.5" />
          <span>
            {dev >= 0 ? '+' : ''}
            {dev.toFixed(1)}%
          </span>
        </div>
      </div>

      {/* comparison bars */}
      <div className="mt-3 space-y-1.5">
        <div className="flex items-center gap-2">
          <span className="text-[9px] font-mono text-cyan-400 w-12 shrink-0">LIVE</span>
          <div className="flex-1 h-2.5 bg-slate-800/80 rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-700 ease-out bg-gradient-to-r from-cyan-500 to-blue-500"
              style={{ width: `${liveW}%` }}
            />
          </div>
          <span className="text-[10px] font-mono text-cyan-300 w-11 text-right tabular-nums">
            {live}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[9px] font-mono text-slate-500 w-12 shrink-0">FORECAST</span>
          <div className="flex-1 h-2.5 bg-slate-800/80 rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-700 ease-out bg-slate-500/70"
              style={{ width: `${predW}%` }}
            />
          </div>
          <span className="text-[10px] font-mono text-slate-400 w-11 text-right tabular-nums">
            {pred}
          </span>
        </div>
      </div>

      {/* on-board train occupancy */}
      <div className="mt-3 pt-3 border-t border-slate-800/70 flex items-center justify-between text-[11px]">
        <span className="text-slate-500 flex items-center gap-1">
          <Train className="w-3 h-3" /> On board
        </span>
        <span className="font-mono text-slate-300 tabular-nums">
          {occ} <span className="text-slate-600">/</span>{' '}
          <span className="text-slate-500">{predOcc} plan</span>
        </span>
      </div>

      {/* delay pressure */}
      <div className="mt-2 flex items-center justify-between text-[11px]">
        <span className="text-slate-500 flex items-center gap-1">
          <Users className="w-3 h-3" /> Late services
        </span>
        <span
          className={`font-mono tabular-nums ${
            pressure.crowd_multiplier > 1.3 ? 'text-red-400' : 'text-slate-400'
          }`}
        >
          {pressure.late_trains}/{pressure.total_trains} · ×{pressure.crowd_multiplier.toFixed(2)}
        </span>
      </div>

      {/* next arrivals */}
      <div className="mt-3 pt-3 border-t border-slate-800/70">
        <p className="text-[9px] font-mono text-slate-500 uppercase tracking-wider mb-1.5">
          Next services
        </p>
        <div className="flex flex-wrap gap-1">
          {nextTrains.length === 0 && (
            <span className="text-[10px] text-slate-600">No services scheduled</span>
          )}
          {nextTrains.map((t) => (
            <span
              key={t.train_id}
              className={`text-[10px] font-mono px-1.5 py-0.5 rounded border ${
                t.delay_min >= 9
                  ? 'bg-red-500/15 text-red-300 border-red-500/30'
                  : t.delay_min >= 3
                    ? 'bg-amber-500/15 text-amber-300 border-amber-500/30'
                    : 'bg-slate-800 text-slate-400 border-slate-700'
              }`}
              title={`${t.line} ${t.direction} — scheduled ${t.scheduled}, actual ${t.actual}`}
            >
              {t.train_id}
              {t.delay_min > 0 && ` +${t.delay_min}`}
            </span>
          ))}
        </div>
      </div>

      {/* anomaly callout */}
      {anomaly && (
        <div className="mt-3 p-2.5 rounded-lg bg-red-500/10 border border-red-500/30 flex items-start gap-2">
          <AlertTriangle className="w-3.5 h-3.5 text-red-400 shrink-0 mt-0.5" />
          <p className="text-[10px] text-red-200 leading-relaxed">
            Live crowd exceeds forecast by{' '}
            <strong className="font-mono">{dev.toFixed(1)}%</strong> (threshold{' '}
            {thresholdPct}%).
          </p>
        </div>
      )}
    </div>
  );
}