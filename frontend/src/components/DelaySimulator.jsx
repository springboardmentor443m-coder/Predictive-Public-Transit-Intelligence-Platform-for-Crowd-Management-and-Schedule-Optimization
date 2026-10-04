import React, { useState, useEffect, useCallback } from 'react';
import {
  CalendarClock,
  AlertTriangle,
  RotateCcw,
  Zap,
  ChevronRight,
  Filter,
} from 'lucide-react';
import {
  fetchTimetable,
  fetchDelayTable,
  injectDelay,
  clearDelay,
  resetDelays,
  fetchLiveNetwork,
} from '../services/api';

const SEVERITY = {
  SEVERE: 'bg-red-500/15 text-red-300 border-red-500/30',
  MODERATE: 'bg-amber-500/15 text-amber-300 border-amber-500/30',
  MINOR: 'bg-slate-700/40 text-slate-300 border-slate-600/50',
  ON_TIME: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20',
};

const STOPS = [
  'Botanical Garden',
  'Dwarka Sec 21',
  'Hauz Khas',
  'Kashmere Gate',
  'Rajiv Chowk',
];

export default function DelaySimulator() {
  const [network, setNetwork] = useState(null);
  const [line, setLine] = useState('');
  const [timetable, setTimetable] = useState([]);
  const [delays, setDelays] = useState(null);
  const [selectedTrainId, setSelectedTrainId] = useState('');
  const [selectedTrain, setSelectedTrain] = useState(null);
  const [injectStation, setInjectStation] = useState('Botanical Garden');
  const [injectMinutes, setInjectMinutes] = useState(10);
  const [busy, setBusy] = useState(false);
  const [toast, setToast] = useState(null);
  const [view, setView] = useState('delays'); // delays | timetable

  // Resolve the chosen service id into a full stop list so the origin-station
  // dropdown can offer exactly the stations that service calls at.
  useEffect(() => {
    if (!selectedTrainId) {
      setSelectedTrain(null);
      return;
    }
    const found = timetable.find((t) => t.train_id === selectedTrainId);
    setSelectedTrain(found || null);
  }, [selectedTrainId, timetable]);

  // Keep the origin station valid for whichever service is targeted.
  useEffect(() => {
    if (!selectedTrain) return;
    const names = selectedTrain.stops.map((s) => s.station);
    if (!names.includes(injectStation)) {
      // prefer a mid-route station, since that produces visible propagation
      setInjectStation(names[Math.min(1, names.length - 1)]);
    }
  }, [selectedTrain]); // eslint-disable-line react-hooks/exhaustive-deps

  const refresh = useCallback(async () => {
    try {
      const [tt, dt] = await Promise.all([
        fetchTimetable(line || null, 120),
        fetchDelayTable(250),
      ]);
      setTimetable(tt.services);
      setDelays(dt);
    } catch (err) {
      setToast({ kind: 'error', text: err.message });
    }
  }, [line]);

  useEffect(() => {
    fetchLiveNetwork()
      .then(setNetwork)
      .catch(() => {});
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const flash = (kind, text) => {
    setToast({ kind, text });
    setTimeout(() => setToast(null), 4000);
  };

  const handleInject = async () => {
    if (!selectedTrain) {
      flash('error', 'Select a train from the timetable first.');
      return;
    }
    setBusy(true);
    try {
      const res = await injectDelay(
        selectedTrain.train_id,
        injectStation,
        injectMinutes
      );
      const chain = res.run.stops
        .map((s) => `${s.station} ${s.delay_min}m`)
        .join('  →  ');
      flash('ok', `${res.message}\n${chain}`);
      setSelectedTrainId('');
      refresh();
    } catch (err) {
      flash('error', err.message);
    } finally {
      setBusy(false);
    }
  };

  const handleReset = async () => {
    setBusy(true);
    try {
      const res = await resetDelays();
      flash('ok', res.message);
      refresh();
    } catch (err) {
      flash('error', err.message);
    } finally {
      setBusy(false);
    }
  };

  // stations this selected train actually serves; the delay-table rows do not
  // carry a stop list, so fall back to the full network
  const servedStations =
    selectedTrain && selectedTrain.stops.length
      ? selectedTrain.stops.map((s) => s.station)
      : STOPS;

  return (
    <div className="space-y-6">
      {/* ---- header + KPIs ---- */}
      <div className="glass-panel rounded-2xl border border-slate-800 p-5">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <CalendarClock className="w-5 h-5 text-cyan-400" />
              Train Schedule & Delay Propagation
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Inject a delay at one station and watch it ripple downstream through
              every other station on that service.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            {delays && (
              <>
                <div className="text-center px-3 py-2 rounded-lg bg-slate-800/60 border border-slate-700">
                  <p className="text-lg font-bold text-white font-display tabular-nums">
                    {delays.total_trains.toLocaleString()}
                  </p>
                  <p className="text-[9px] text-slate-500 font-mono uppercase">services</p>
                </div>
                <div className="text-center px-3 py-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
                  <p className="text-lg font-bold text-emerald-300 font-display tabular-nums">
                    {delays.on_time_pct}%
                  </p>
                  <p className="text-[9px] text-emerald-500/70 font-mono uppercase">on time</p>
                </div>
                <div className="text-center px-3 py-2 rounded-lg bg-red-500/10 border border-red-500/20">
                  <p className="text-lg font-bold text-red-300 font-display tabular-nums">
                    {delays.severity_breakdown.SEVERE}
                  </p>
                  <p className="text-[9px] text-red-500/70 font-mono uppercase">severe</p>
                </div>
                <div className="text-center px-3 py-2 rounded-lg bg-amber-500/10 border border-amber-500/20">
                  <p className="text-lg font-bold text-amber-300 font-display tabular-nums">
                    {delays.mean_delay_min}m
                  </p>
                  <p className="text-[9px] text-amber-500/70 font-mono uppercase">
                    mean delay
                  </p>
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      {/* ---- toast ---- */}
      {toast && (
        <div
          className={`rounded-xl border p-3 text-xs font-mono whitespace-pre-line ${
            toast.kind === 'ok'
              ? 'bg-emerald-500/10 border-emerald-500/40 text-emerald-200'
              : 'bg-red-500/10 border-red-500/40 text-red-200'
          }`}
        >
          {toast.text}
        </div>
      )}

      {/* ---- injection panel ---- */}
      <div className="glass-panel rounded-2xl border border-cyan-500/20 p-5">
        <div className="flex items-center gap-2 mb-4">
          <Zap className="w-4 h-4 text-cyan-400" />
          <h3 className="text-sm font-bold text-white">Delay Simulator</h3>
        </div>

        {!selectedTrain ? (
          <p className="text-xs text-amber-200/90 bg-amber-500/10 border border-amber-500/30 rounded-lg px-3 py-2 flex items-center gap-2 mb-4">
            <Zap className="w-3.5 h-3.5 shrink-0" />
            Pick a target service below to enable injection &mdash; or click any
            row in the delay table / timetable.
          </p>
        ) : (
          <div className="mb-4 p-3 rounded-xl bg-slate-900/70 border border-cyan-500/20">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <div>
                <p className="text-sm font-bold text-white font-mono">
                  {selectedTrain.train_id}
                </p>
                <p className="text-[10px] text-slate-400">
                  {selectedTrain.line} &middot; {selectedTrain.direction} &middot;{' '}
                  {selectedTrain.capacity} pax rake
                </p>
              </div>
              <button
                onClick={() => setSelectedTrainId('')}
                className="text-[10px] text-slate-400 hover:text-white font-mono px-2 py-1 rounded border border-slate-700 hover:border-slate-500"
              >
                clear
              </button>
            </div>

            <div className="mt-2 flex flex-wrap gap-1">
              {selectedTrain.stops.map((s, i) => {
                const originIdx = selectedTrain.stops.findIndex(
                  (x) => x.station === injectStation
                );
                const isOrigin = i === originIdx;
                // preview what each stop WILL carry once injected
                const inherited =
                  i < originIdx ? 0 : Math.max(0, injectMinutes - (i - originIdx));
                const shown = Math.max(s.delay_min, inherited);
                return (
                  <span key={i} className="flex items-center gap-1">
                    <span
                      className={`text-[10px] font-mono px-1.5 py-0.5 rounded border ${
                        isOrigin
                          ? 'bg-cyan-500/25 text-cyan-100 border-cyan-400 ring-1 ring-cyan-400'
                          : shown >= 9
                            ? 'bg-red-500/20 text-red-200 border-red-500/40'
                            : shown >= 3
                              ? 'bg-amber-500/20 text-amber-200 border-amber-500/40'
                              : 'bg-slate-800 text-slate-400 border-slate-700'
                      }`}
                      title={
                        isOrigin
                          ? 'origin - delay injected here'
                          : shown > 0
                            ? `will inherit ${shown} min`
                            : 'upstream, unaffected'
                      }
                    >
                      {s.station.split(' ')[0]} {s.scheduled}
                      {shown > 0 && ` +${shown}`}
                    </span>
                    {i < selectedTrain.stops.length - 1 && (
                      <ChevronRight className="w-3 h-3 text-slate-600" />
                    )}
                  </span>
                );
              })}
            </div>
            <p className="text-[9px] font-mono text-slate-500 mt-2">
              cyan = origin &middot; red/amber = inherits the delay (1 min
              recovered per leg) &middot; grey = upstream, unaffected
            </p>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-3 items-end">
          <div className="lg:col-span-2">
            <label className="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
              Target service
            </label>
            <select
              value={selectedTrainId}
              onChange={(e) => setSelectedTrainId(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 font-mono focus:outline-none focus:border-cyan-500"
            >
              <option value="">
                {timetable.length
                  ? `-- pick a service (${timetable.length} shown) --`
                  : '-- loading services --'}
              </option>
              {timetable.map((t) => {
                const worst = Math.max(...t.stops.map((s) => s.delay_min));
                return (
                  <option key={t.train_id} value={t.train_id}>
                    {t.train_id} &middot; {t.scheduled_departure} &middot;{' '}
                    {t.line.replace(' Line', '')} {t.direction}
                    {worst > 0 ? ` (already +${worst}m)` : ''}
                  </option>
                );
              })}
            </select>
          </div>

          <div>
            <label className="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
              Origin station
            </label>
            <select
              value={injectStation}
              onChange={(e) => setInjectStation(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 font-mono focus:outline-none focus:border-cyan-500 disabled:opacity-40"
              disabled={!selectedTrain}
            >
              {servedStations.map((s, i) => (
                <option key={s} value={s}>
                  {s}
                  {i === 0 ? ' (terminus)' : ''}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
              Delay (minutes) &mdash; {injectMinutes}
            </label>
            <input
              type="range"
              min="1"
              max="45"
              value={injectMinutes}
              onChange={(e) => setInjectMinutes(Number(e.target.value))}
              className="w-full accent-cyan-500 disabled:opacity-40"
              disabled={!selectedTrain}
            />
            <p className="text-[9px] font-mono text-slate-500 mt-0.5">
              1&ndash;45 min, decays 1 min per station served
            </p>
          </div>
        </div>

        <div className="flex gap-2 mt-4">
          <button
            onClick={handleInject}
            disabled={!selectedTrain || busy}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 text-white text-xs font-bold disabled:opacity-40 disabled:cursor-not-allowed enabled:hover:shadow-lg enabled:hover:shadow-cyan-500/25 transition-all"
          >
            <Zap className="w-3.5 h-3.5" />
            {busy ? 'Injecting\u2026' : 'Inject Delay'}
          </button>
          <button
            onClick={handleReset}
            disabled={busy}
            className="px-4 py-2.5 rounded-lg bg-slate-800 border border-slate-700 text-slate-300 text-xs font-semibold hover:bg-slate-700 disabled:opacity-40 flex items-center gap-1.5"
            title="Restore the whole network to its baseline timetable"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            Reset all
          </button>
        </div>
      </div>

      {/* ---- view switcher ---- */}
      <div className="flex items-center gap-2 flex-wrap">
        <div className="flex p-1 rounded-xl bg-slate-900/90 border border-slate-800">
          {[
            { id: 'delays', label: `Delay Table (${delays?.late_trains ?? 0})` },
            { id: 'timetable', label: `Timetable (${timetable.length})` },
          ].map((t) => (
            <button
              key={t.id}
              onClick={() => setView(t.id)}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                view === t.id
                  ? 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        <select
          value={line}
          onChange={(e) => setLine(e.target.value)}
          className="bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-200 font-mono focus:outline-none focus:border-cyan-500"
        >
          <option value="">All lines</option>
          {(network?.lines || []).map((l) => (
            <option key={l.name} value={l.name}>
              {l.name}
            </option>
          ))}
        </select>
      </div>

      {/* ---- delay table ---- */}
      {view === 'delays' && (
        <div className="glass-panel rounded-2xl border border-slate-800 overflow-hidden">
          <div className="p-3 border-b border-slate-800 flex items-center justify-between">
            <h3 className="text-xs font-bold text-white flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-400" />
              Delay Register — sorted by scheduled departure
            </h3>
            <span className="text-[10px] text-slate-500 font-mono">
              click a row to target that service
            </span>
          </div>
          <div className="max-h-[520px] overflow-y-auto">
            <table className="w-full text-[11px] font-mono">
              <thead className="sticky top-0 bg-slate-900/95 backdrop-blur z-10">
                <tr className="text-slate-400 text-left">
                  <th className="px-3 py-2 font-semibold">Service</th>
                  <th className="px-3 py-2 font-semibold">Line</th>
                  <th className="px-3 py-2 font-semibold">Sched</th>
                  <th className="px-3 py-2 font-semibold">Actual</th>
                  <th className="px-3 py-2 font-semibold text-right">Delay</th>
                  <th className="px-3 py-2 font-semibold">Origin</th>
                  <th className="px-3 py-2 font-semibold">Severity</th>
                </tr>
              </thead>
              <tbody>
                {!delays?.rows.length && (
                  <tr>
                    <td colSpan={7} className="px-3 py-8 text-center text-slate-500">
                      No delays — entire network running to timetable
                    </td>
                  </tr>
                )}
                {delays?.rows.map((r) => (
                  <tr
                    key={r.train_id}
                    onClick={() => setSelectedTrainId(r.train_id)}
                    title="Select this service as the injection target"
                    className={`border-t border-slate-800/60 hover:bg-slate-800/40 cursor-pointer transition-colors ${
                      selectedTrainId === r.train_id ? 'bg-cyan-500/10' : ''
                    }`}
                  >
                    <td className="px-3 py-2 text-cyan-300 font-semibold">
                      {r.train_id}
                    </td>
                    <td className="px-3 py-2 text-slate-400">{r.line.replace(' Line', '')}</td>
                    <td className="px-3 py-2 text-slate-400">{r.scheduled_departure}</td>
                    <td className="px-3 py-2 text-slate-200">{r.actual_departure}</td>
                    <td className="px-3 py-2 text-right font-bold text-red-400 tabular-nums">
                      +{r.delay_min}m
                    </td>
                    <td className="px-3 py-2 text-slate-400">{r.origin_station}</td>
                    <td className="px-3 py-2">
                      <span
                        className={`px-1.5 py-0.5 rounded border text-[10px] font-bold ${SEVERITY[r.severity]}`}
                      >
                        {r.severity}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ---- timetable ---- */}
      {view === 'timetable' && (
        <div className="glass-panel rounded-2xl border border-slate-800 overflow-hidden">
          <div className="p-3 border-b border-slate-800 flex items-center justify-between">
            <h3 className="text-xs font-bold text-white flex items-center gap-2">
              <Filter className="w-4 h-4 text-cyan-400" />
              Scheduled Services — click to inject a delay
            </h3>
            <span className="text-[10px] text-slate-500 font-mono">
              showing {timetable.length}
              {line ? ` of ${line}` : ''}
            </span>
          </div>
          <div className="max-h-[520px] overflow-y-auto divide-y divide-slate-800/60">
            {timetable.map((t) => {
              const isSel = selectedTrain?.train_id === t.train_id;
              const worst = Math.max(...t.stops.map((s) => s.delay_min));
              return (
                <button
                  key={t.train_id}
                  onClick={() => setSelectedTrainId(t.train_id)}
                  className={`w-full text-left px-3 py-2.5 hover:bg-slate-800/40 transition-colors ${
                    isSel ? 'bg-cyan-500/10 border-l-2 border-cyan-400' : 'border-l-2 border-transparent'
                  }`}
                >
                  <div className="flex items-center justify-between gap-3 mb-1.5">
                    <div className="flex items-center gap-2 min-w-0">
                      <span className="text-[11px] font-bold text-cyan-300 font-mono">
                        {t.train_id}
                      </span>
                      <span className="text-[10px] text-slate-400 truncate">
                        {t.line} · {t.direction}
                      </span>
                      <span className="text-[10px] text-slate-600 font-mono shrink-0">
                        {t.capacity} pax
                      </span>
                    </div>
                    {worst > 0 && (
                      <span className="text-[10px] font-bold text-red-400 font-mono shrink-0">
                        +{worst}m worst
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-1 overflow-x-auto">
                    {t.stops.map((s, i) => (
                      <React.Fragment key={i}>
                        <div className="shrink-0 text-center">
                          <div
                            className={`text-[9px] font-mono px-1.5 py-0.5 rounded border ${
                              s.delay_min >= 9
                                ? 'bg-red-500/20 text-red-200 border-red-500/40'
                                : s.delay_min >= 3
                                  ? 'bg-amber-500/20 text-amber-200 border-amber-500/40'
                                  : 'bg-slate-800 text-slate-300 border-slate-700'
                            }`}
                          >
                            {s.scheduled}
                            {s.delay_min > 0 && (
                              <span className="ml-0.5 font-bold">+{s.delay_min}</span>
                            )}
                          </div>
                          <p className="text-[8px] text-slate-500 mt-0.5 truncate max-w-[70px]">
                            {s.station.split(' ')[0]}
                          </p>
                        </div>
                        {i < t.stops.length - 1 && (
                          <ChevronRight className="w-2.5 h-2.5 text-slate-700 shrink-0 mt-1" />
                        )}
                      </React.Fragment>
                    ))}
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}