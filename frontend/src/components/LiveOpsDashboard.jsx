import React, { useMemo } from 'react';
import { Radio, Users, Bell, Activity, TrendingUp, Clock, Zap } from 'lucide-react';
import { useLiveSocket } from '../hooks/useLiveSocket';
import StationCrowdCard from './StationCrowdCard';

function StatTile({ label, value, sub, icon: Icon, tone = 'cyan' }) {
  const tones = {
    cyan: 'text-cyan-400 bg-cyan-500/10 border-cyan-500/20',
    red: 'text-red-400 bg-red-500/10 border-red-500/20',
    amber: 'text-amber-400 bg-amber-500/10 border-amber-500/20',
    emerald: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
    slate: 'text-slate-400 bg-slate-800/60 border-slate-700',
  };
  return (
    <div className="glass-panel rounded-xl border border-slate-800 p-4 flex items-center gap-3">
      <div className={`p-2.5 rounded-lg border shrink-0 ${tones[tone]}`}>
        <Icon className="w-4 h-4" />
      </div>
      <div className="min-w-0">
        <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">
          {label}
        </p>
        <p className="text-xl font-bold text-white font-display tabular-nums leading-tight">
          {value}
        </p>
        {sub && <p className="text-[10px] text-slate-500 font-mono truncate">{sub}</p>}
      </div>
    </div>
  );
}

export default function LiveOpsDashboard() {
  const { snapshot, status, error } = useLiveSocket();

  const sortedStations = useMemo(() => {
    if (!snapshot) return [];
    return [...snapshot.stations].sort(
      (a, b) => b.live_platform_crowd - a.live_platform_crowd
    );
  }, [snapshot]);

  if (!snapshot) {
    return (
      <div className="glass-panel rounded-2xl border border-slate-800 p-12 text-center">
        <Radio className="w-10 h-10 text-cyan-400 mx-auto mb-3 animate-pulse" />
        <p className="text-sm text-slate-400 font-mono">
          {error ? `Live feed unavailable: ${error}` : 'Connecting to live crowd feed…'}
        </p>
      </div>
    );
  }

  const totals = snapshot.network_totals;
  const threshold = snapshot.anomaly_threshold_pct;
  const statusTone =
    status === 'live' ? 'emerald' : status === 'polling' ? 'amber' : 'red';
  const statusLabel =
    status === 'live'
      ? 'WebSocket live'
      : status === 'polling'
        ? 'Polling fallback'
        : 'Disconnected';

  return (
    <div className="space-y-6">
      {/* ---- connection + clock banner ---- */}
      <div className="glass-panel rounded-2xl border border-slate-800 p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="relative">
            <div
              className={`w-2.5 h-2.5 rounded-full ${
                status === 'live'
                  ? 'bg-emerald-400 radar-pulse'
                  : status === 'polling'
                    ? 'bg-amber-400'
                    : 'bg-red-500'
              }`}
            />
          </div>
          <div>
            <p className="text-xs font-semibold text-slate-200">{statusLabel}</p>
            <p className="text-[10px] text-slate-500 font-mono">
              Streaming every 2s · frame #{snapshot.tick}
              {status !== 'live' && ' · reconnecting…'}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Clock className="w-4 h-4 text-cyan-400" />
          <span className="text-2xl font-black text-white font-display tabular-nums">
            {snapshot.sim_time_label}
          </span>
          <span
            className={`text-[10px] font-bold px-2 py-0.5 rounded border font-mono ${
              snapshot.is_peak_hour
                ? 'bg-red-500/15 text-red-300 border-red-500/30'
                : 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30'
            }`}
          >
            {snapshot.is_peak_hour ? 'PEAK' : 'OFF-PEAK'}
          </span>
        </div>
      </div>

      {/* ---- warnings: live crowd above forecast ---- */}
      {snapshot.warnings.length > 0 && (
        <div className="space-y-2">
          {snapshot.warnings.map((w) => (
            <div
              key={w.station}
              className={`rounded-2xl border p-4 flex items-start gap-3 animate-pulse-once ${
                w.severity === 'CRITICAL'
                  ? 'bg-red-500/10 border-red-500/40'
                  : 'bg-amber-500/10 border-amber-500/40'
              }`}
            >
              <div
                className={`p-2 rounded-lg shrink-0 border ${
                  w.severity === 'CRITICAL'
                    ? 'bg-red-500/20 text-red-300 border-red-500/40'
                    : 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                }`}
              >
                <Bell className="w-4 h-4" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <span
                    className={`text-[10px] font-black px-2 py-0.5 rounded font-mono tracking-wider ${
                      w.severity === 'CRITICAL'
                        ? 'bg-red-500 text-white'
                        : 'bg-amber-500 text-slate-900'
                    }`}
                  >
                    {w.severity}
                  </span>
                  <span className="text-sm font-bold text-white">{w.station}</span>
                </div>
                <p className="text-xs text-slate-200 mt-1.5 leading-relaxed">
                  {w.message}
                </p>
                <p className="text-[10px] text-slate-400 mt-1 font-mono">
                  Likely cause: {w.likely_cause}
                </p>
              </div>
              <div className="text-right shrink-0">
                <p className="text-xl font-black text-white font-display tabular-nums">
                  +{w.deviation_pct.toFixed(0)}%
                </p>
                <p className="text-[9px] text-slate-500 font-mono">vs forecast</p>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ---- network totals ---- */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatTile
          label="Live crowd"
          value={totals.live_crowd.toLocaleString()}
          sub="waiting across all 5 stations"
          icon={Users}
          tone="cyan"
        />
        <StatTile
          label="ML forecast"
          value={totals.predicted_crowd.toLocaleString()}
          sub={`expected at ${snapshot.sim_time_label}`}
          icon={TrendingUp}
          tone="slate"
        />
        <StatTile
          label="Busiest station"
          value={totals.peak_station}
          sub="highest live platform crowd"
          icon={Activity}
          tone="amber"
        />
        <StatTile
          label="Active alerts"
          value={snapshot.warnings.length}
          sub={`threshold ${threshold}% above forecast`}
          icon={Bell}
          tone={snapshot.warnings.length ? 'red' : 'emerald'}
        />
      </div>

      {/* ---- per-station live vs forecast ---- */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Users className="w-4 h-4 text-cyan-400" />
            Station Crowd — Live vs Forecast
          </h3>
          <p className="text-[10px] text-slate-500 font-mono">
            live source: {snapshot.stations[0]?.historical_samples ?? 0} historical
            samples re-dated to today
          </p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
          {sortedStations.map((s) => (
            <StationCrowdCard key={s.station} station={s} thresholdPct={threshold} />
          ))}
        </div>
      </div>

      {/* ---- provenance note ---- */}
      <div className="glass-panel rounded-2xl border border-slate-800 p-4">
        <div className="flex items-start gap-3">
          <Zap className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <div className="text-[11px] text-slate-400 leading-relaxed">
            <p className="text-slate-300 font-semibold mb-1">
              Where these live numbers come from
            </p>
            Every reading is a real row of{' '}
            <code className="text-cyan-400 font-mono">
              AI_MetroFlow_Master_Dataset.xlsx
            </code>{' '}
            (5,000 trips spanning all of 2023) re-dated onto today&rsquo;s calendar
            — same month-day and time-of-day, so the live feed is observed history
            rather than invented noise. Delay pressure is applied on top: when
            services run late, passengers cannot board, so platform crowd compounds.
            Season factor today:{' '}
            <span className="text-amber-400 font-mono">
              ×{snapshot.season_factor}
            </span>
            .
          </div>
        </div>
      </div>
    </div>
  );
}