import React, { useEffect, useState } from 'react';
import { Train, Loader2, MapPin, ChevronRight, Search } from 'lucide-react';
import { resolveService } from '../services/api';

/**
 * Resolves the current prediction scenario against today's timetable and shows
 * the physical service it refers to.
 *
 * Without this the station pickers look like a generic route selector, and
 * there is no way to tell which train the forecast is actually about.
 */
export default function ServiceDetails({
  fromStation,
  toStation,
  lineName,
  hour,
  compact = false,
}) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!fromStation || !toStation || fromStation === toStation) {
      setData(null);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError(null);

    resolveService({ fromStation, toStation, line: lineName, hour })
      .then((d) => {
        if (!cancelled) setData(d);
      })
      .catch((e) => {
        if (!cancelled) {
          setError(e.message);
          setData(null);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [fromStation, toStation, lineName, hour]);

  if (!fromStation || !toStation) return null;

  if (fromStation === toStation) {
    return (
      <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 px-3 py-2.5">
        <p className="text-[11px] font-mono text-amber-200">
          Origin and destination are the same station — pick a different
          destination to resolve a scheduled service.
        </p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-[11px] font-mono text-slate-400 px-1 py-1">
        <Loader2 className="w-3.5 h-3.5 animate-spin" />
        Resolving scheduled service…
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-xl border border-red-500/30 bg-red-500/10 px-3 py-2.5">
        <p className="text-[11px] font-mono text-red-200">
          Could not resolve a service: {error}
        </p>
      </div>
    );
  }

  if (!data) return null;

  if (data.found === false) {
    return (
      <div className="rounded-xl border border-slate-700 bg-slate-900/60 px-3 py-2.5">
        <p className="text-[11px] font-mono text-slate-400">
          No scheduled service runs {fromStation} → {toStation}
          {lineName ? ` on the ${lineName}` : ''}.
        </p>
      </div>
    );
  }

  const delayed = data.current_delay_min > 0;

  return (
    <div className="rounded-xl border border-cyan-500/25 bg-slate-900/70 p-3">
      {/* header row */}
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div className="flex items-start gap-2.5 min-w-0">
          <div
            className={`p-2 rounded-lg border shrink-0 ${
              delayed
                ? 'bg-amber-500/10 text-amber-400 border-amber-500/25'
                : 'bg-cyan-500/10 text-cyan-400 border-cyan-500/25'
            }`}
          >
            <Train className="w-4 h-4" />
          </div>
          <div className="min-w-0">
            <p className="text-[9px] font-mono text-slate-500 uppercase tracking-wider flex items-center gap-1">
              <Search className="w-2.5 h-2.5" />
              Forecast refers to this service
            </p>
            <p className="text-sm font-bold text-white font-mono leading-tight">
              {data.train_id}
            </p>
            <p className="text-[10px] text-slate-400">
              {data.line} · {data.direction} · {data.capacity} pax rake
            </p>
          </div>
        </div>

        <div className="text-right shrink-0">
          <p className="text-[9px] font-mono text-slate-500 uppercase">
            Scheduled
          </p>
          <p className="text-sm font-bold text-cyan-300 font-mono tabular-nums leading-tight">
            {data.scheduled_departure} → {data.scheduled_arrival}
          </p>
          <p
            className={`text-[10px] font-mono font-semibold ${
              delayed ? 'text-amber-400' : 'text-emerald-400'
            }`}
          >
            {delayed ? `running +${data.current_delay_min}m` : 'on time'}
          </p>
        </div>
      </div>

      {/* stop chain */}
      <div className="mt-2.5 pt-2.5 border-t border-slate-800/70 flex flex-wrap items-center gap-1">
        {data.legs.map((leg, i) => (
          <React.Fragment key={i}>
            <span className="flex flex-col items-center">
              <span
                className={`text-[9px] font-mono px-1.5 py-0.5 rounded border whitespace-nowrap ${
                  leg.delay_min >= 9
                    ? 'bg-red-500/20 text-red-200 border-red-500/40'
                    : leg.delay_min >= 3
                      ? 'bg-amber-500/20 text-amber-200 border-amber-500/40'
                      : 'bg-slate-800 text-slate-300 border-slate-700'
                }`}
                title={`${leg.station} — scheduled ${leg.scheduled}${
                  leg.delay_min ? `, actual ${leg.actual}` : ''
                }`}
              >
                {leg.scheduled}
                {leg.delay_min > 0 && ` +${leg.delay_min}`}
              </span>
              <span className="text-[8px] text-slate-500 mt-0.5 flex items-center gap-0.5">
                <MapPin className="w-2 h-2" />
                {leg.station.split(' ')[0]}
              </span>
            </span>
            {i < data.legs.length - 1 && (
              <ChevronRight className="w-2.5 h-2.5 text-slate-700 shrink-0 mt-3" />
            )}
          </React.Fragment>
        ))}
      </div>

      {!compact && (
        <p className="text-[9px] font-mono text-slate-500 mt-2">
          {data.candidates_today} service
          {data.candidates_today === 1 ? '' : 's'} run this route today · showing
          the closest to {String(hour ?? '--').padStart(2, '0')}:00
        </p>
      )}
    </div>
  );
}