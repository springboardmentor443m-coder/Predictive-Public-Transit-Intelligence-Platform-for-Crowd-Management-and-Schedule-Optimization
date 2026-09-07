import { congestionColor } from "./StatusBadge";

export default function HeatmapGrid({ points, stations, onSelectStation }) {
  if (!points || !points.length) {
    return <div className="py-10 text-center text-sm text-slate-400">Loading heatmap…</div>;
  }

  const byHour = {};
  for (const p of points) {
    (byHour[p.hour] = byHour[p.hour] || []).push(p);
  }
  const hours = Array.from({ length: 24 }, (_, i) => i);

  return (
    <div className="overflow-x-auto">
      <table className="border-separate" style={{ borderSpacing: "2px" }}>
        <thead>
          <tr>
            <th className="sticky left-0 z-10 bg-white px-2 py-1 text-left text-[11px] font-semibold uppercase text-slate-500">
              Station
            </th>
            {hours.map((h) => (
              <th key={h} className="w-6 px-0 py-1 text-center text-[9px] font-medium text-slate-400">
                {h % 3 === 0 ? h : ""}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {(stations || Object.values(byHour)[0]?.map((p) => ({ id: p.station_id, name: p.station_name })) || []).map(
            (st) => (
              <tr key={st.id}>
                <td
                  onClick={() => onSelectStation && onSelectStation(st.id)}
                  className={`sticky left-0 z-10 whitespace-nowrap bg-white px-2 py-1 text-xs font-medium text-slate-700 ${
                    onSelectStation ? "cursor-pointer hover:text-brand-600" : ""
                  }`}
                >
                  {st.name}
                </td>
                {hours.map((h) => {
                  const cell = byHour[h]?.find((p) => p.station_id === st.id);
                  const pct = cell?.occupancy_pct ?? 0;
                  return (
                    <td key={h} className="p-0">
                      <div
                        title={`${st.name} · ${String(h).padStart(2, "0")}:00 · ${pct}%`}
                        className="h-6 w-6 rounded-[4px] transition-transform hover:scale-125"
                        style={{ backgroundColor: congestionColor(pct), opacity: 0.25 + Math.min(1, pct / 100) * 0.75 }}
                      />
                    </td>
                  );
                })}
              </tr>
            )
          )}
        </tbody>
      </table>
      <div className="mt-3 flex items-center gap-4 text-xs text-slate-500">
        <span className="font-semibold">Congestion:</span>
        {[
          ["Low", "#10b981"],
          ["Medium", "#f59e0b"],
          ["High", "#f97316"],
          ["Critical", "#e11d48"],
        ].map(([label, color]) => (
          <span key={label} className="inline-flex items-center gap-1.5">
            <span className="h-3 w-3 rounded-sm" style={{ backgroundColor: color }} />
            {label}
          </span>
        ))}
      </div>
    </div>
  );
}
