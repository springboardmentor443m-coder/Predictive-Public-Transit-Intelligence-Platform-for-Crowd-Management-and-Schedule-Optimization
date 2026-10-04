import React, { useMemo, useState } from 'react';

/**
 * Station x hour error heatmap.
 *
 * Colour encodes MAE (how badly the model predicts that cell) and the bar
 * underneath encodes bias (whether the model over- or under-predicts).
 * Cells with too few test samples are hatched out rather than shown as a
 * misleading zero.
 */
export default function ErrorHeatmap({ heatmap }) {
  const [hover, setHover] = useState(null);

  const { hours, rows, flat } = useMemo(() => {
    const hours = heatmap.hours;
    const rows = heatmap.rows;
    const vals = [];
    rows.forEach((r) =>
      r.cells.forEach((c) => {
        if (c) vals.push(c.mae);
      })
    );
    return { hours, rows, flat: vals };
  }, [heatmap]);

  const min = flat.length ? Math.min(...flat) : 0;
  const max = flat.length ? Math.max(...flat) : 1;
  const span = max - min || 1;

  // green (accurate) -> amber -> red (inaccurate)
  function cellColor(mae) {
    const t = (mae - min) / span; // 0..1
    if (t < 0.5) {
      const k = t / 0.5;
      const r = Math.round(16 + k * 160);
      const g = Math.round(185 - k * 70);
      const b = Math.round(129 - k * 70);
      return `rgba(${r}, ${g}, ${b}, ${0.18 + k * 0.35})`;
    }
    const k = (t - 0.5) / 0.5;
    const r = Math.round(176 + k * 68);
    const g = Math.round(115 - k * 65);
    const b = Math.round(59 - k * 40);
    return `rgba(${r}, ${g}, ${b}, ${0.18 + k * 0.45})`;
  }

  function textColor(mae) {
    const t = (mae - min) / span;
    return t > 0.62 ? 'text-slate-950' : 'text-slate-200';
  }

  return (
    <div>
      <div className="flex items-start gap-3 mb-3">
        <div className="flex-1 overflow-x-auto">
          <table className="border-separate border-spacing-0.5">
            <thead>
              <tr>
                <th className="text-[9px] font-mono text-slate-500 text-left pr-2 font-semibold">
                  Station
                </th>
                {hours.map((h) => (
                  <th
                    key={h}
                    className="text-[8px] font-mono text-slate-500 font-semibold px-0.5 pb-1"
                  >
                    {String(h).padStart(2, '0')}
                  </th>
                ))}
                <th className="text-[9px] font-mono text-slate-400 pl-2 font-semibold">
                  Avg
                </th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => {
                const present = r.cells.filter(Boolean);
                const rowAvg = present.length
                  ? present.reduce((a, c) => a + c.mae, 0) / present.length
                  : null;
                return (
                  <tr key={r.station}>
                    <td className="text-[9px] font-mono text-slate-300 pr-2 whitespace-nowrap">
                      {r.station}
                    </td>
                    {r.cells.map((c, i) => {
                      const isHover = hover?.station === r.station && hover?.hour === hours[i];
                      if (!c) {
                        return (
                          <td key={i} className="px-0.5">
                            <div
                              className="w-7 h-6 rounded-[3px] border border-slate-800"
                              style={{
                                backgroundImage:
                                  'repeating-linear-gradient(45deg, transparent, transparent 3px, rgba(100,116,139,0.15) 3px, rgba(100,116,139,0.15) 6px)',
                              }}
                              title={`${r.station} ${String(hours[i]).padStart(2, '0')}:00 — too few samples`}
                            />
                          </td>
                        );
                      }
                      return (
                        <td key={i} className="px-0.5">
                          <div
                            onMouseEnter={() =>
                              setHover({ station: r.station, hour: hours[i], cell: c })
                            }
                            onMouseLeave={() => setHover(null)}
                            className={`w-7 h-6 rounded-[3px] flex items-center justify-center text-[8px] font-mono font-semibold tabular-nums cursor-default transition-all ${
                              isHover ? 'ring-1 ring-white/70 scale-110' : ''
                            } ${textColor(c.mae)}`}
                            style={{ backgroundColor: cellColor(c.mae) }}
                            title={`${r.station} ${String(hours[i]).padStart(2, '0')}:00 — MAE ${c.mae}, bias ${c.bias}, n=${c.n}`}
                          >
                            {c.mae >= 100 ? Math.round(c.mae) : c.mae.toFixed(0)}
                          </div>
                        </td>
                      );
                    })}
                    <td className="pl-2 text-[9px] font-mono font-semibold text-cyan-300 tabular-nums">
                      {rowAvg ? rowAvg.toFixed(0) : '—'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* legend */}
        <div className="shrink-0">
          <p className="text-[8px] font-mono text-slate-500 uppercase mb-1">MAE</p>
          <div
            className="w-3 h-28 rounded border border-slate-700"
            style={{
              background: `linear-gradient(to top, rgba(16,185,129,0.5), rgba(176,115,59,0.4), rgba(244,50,50,0.65))`,
            }}
          />
          <div className="flex flex-col justify-between h-28 mt-0.5">
            <span className="text-[8px] font-mono text-slate-400">{max.toFixed(0)}</span>
            <span className="text-[8px] font-mono text-slate-600">
              {(max / 2).toFixed(0)}
            </span>
            <span className="text-[8px] font-mono text-slate-400">{min.toFixed(0)}</span>
          </div>
        </div>
      </div>

      {/* hover readout */}
      <div className="mt-2 p-2 rounded-lg bg-slate-900/70 border border-slate-800 min-h-[34px]">
        {hover ? (
          <p className="text-[10px] font-mono text-slate-300">
            <span className="text-cyan-300 font-semibold">{hover.station}</span>
            {' '}at {String(hover.hour).padStart(2, '0')}:00 —{' '}
            <span className="text-amber-300">MAE {hover.cell.mae}</span> ·{' '}
            <span
              className={
                hover.cell.bias >= 0 ? 'text-red-400' : 'text-emerald-400'
              }
            >
              bias {hover.cell.bias > 0 ? '+' : ''}
              {hover.cell.bias}
            </span>{' '}
            · {hover.cell.n} test samples
          </p>
        ) : (
          <p className="text-[10px] font-mono text-slate-500">
            Hover a cell for exact figures. Colour = MAE (green = accurate, red
            = worst). Hatch pattern = too few samples to judge.
          </p>
        )}
      </div>
    </div>
  );
}