import { useState } from "react";
import { congestionColor } from "./StatusBadge";

export default function HeatmapGrid({ points, stations, onSelectStation }) {
  const [query, setQuery] = useState("");

  if (!points || !points.length) {
    return (
      <div className="py-12 text-center text-sm text-slate-500 flex items-center justify-center">
        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-brand-500 mr-2" />
        Generating 24-hour station congestion heatmap...
      </div>
    );
  }

  const byHour = {};
  for (const p of points) {
    (byHour[p.hour] = byHour[p.hour] || []).push(p);
  }
  const hours = Array.from({ length: 24 }, (_, i) => i);

  const allStations = (
    stations ||
    Object.values(byHour)[0]?.map((p) => ({ id: p.station_id, name: p.station_name })) ||
    []
  );

  const filteredStations = allStations.filter(
    (st) => st.name.toLowerCase().includes(query.toLowerCase()) || st.id.toLowerCase().includes(query.toLowerCase())
  );

  return (
    <div className="space-y-3">
      {/* Header controls */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="relative">
          <input
            type="text"
            placeholder="Filter stations in heatmap..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="input py-1 px-3 text-xs w-56"
          />
        </div>
        <span className="text-xs text-slate-400">
          Showing {filteredStations.length} of {allStations.length} stations
        </span>
      </div>

      {/* Heatmap Table */}
      <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-950/80 p-3">
        <table className="border-separate min-w-full" style={{ borderSpacing: "3px" }}>
          <thead>
            <tr>
              <th className="sticky left-0 z-20 bg-slate-950 px-3 py-1.5 text-left text-[11px] font-extrabold uppercase tracking-wider text-slate-400">
                Station
              </th>
              {hours.map((h) => (
                <th key={h} className="w-7 px-0 py-1 text-center text-[10px] font-mono font-bold text-slate-400">
                  {h % 3 === 0 ? `${String(h).padStart(2, "0")}` : "•"}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filteredStations.map((st) => (
              <tr key={st.id} className="group">
                <td
                  onClick={() => onSelectStation && onSelectStation(st.id)}
                  className={`sticky left-0 z-20 whitespace-nowrap bg-slate-950 px-3 py-1 text-xs font-bold text-slate-200 transition ${
                    onSelectStation ? "cursor-pointer group-hover:text-brand-400" : ""
                  }`}
                >
                  {st.name}
                </td>
                {hours.map((h) => {
                  const cell = byHour[h]?.find((p) => p.station_id === st.id);
                  const pct = cell?.occupancy_pct ?? 0;
                  const color = congestionColor(pct);

                  return (
                    <td key={h} className="p-0">
                      <div
                        title={`${st.name} (${st.id})\nHour: ${String(h).padStart(2, "0")}:00 - ${String(h + 1).padStart(2, "0")}:00\nAverage Occupancy: ${pct}%\nStatus: ${cell?.congestion_level || "low"}`}
                        className="h-6 w-7 rounded-[4px] transition-all duration-200 hover:scale-125 hover:z-30 hover:shadow-lg hover:ring-2 hover:ring-white"
                        style={{
                          backgroundColor: color,
                          opacity: 0.3 + Math.min(1, pct / 100) * 0.7,
                        }}
                      />
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Heatmap Legend */}
      <div className="flex flex-wrap items-center justify-between gap-4 text-xs text-slate-400 pt-1">
        <div className="flex items-center gap-3">
          <span className="font-extrabold uppercase text-slate-400">Density Spectrum:</span>
          {[
            ["Low <55%", "#10b981"],
            ["Medium 55-75%", "#eab308"],
            ["High 75-90%", "#f97316"],
            ["Critical ≥90%", "#f43f5e"],
          ].map(([label, color]) => (
            <span key={label} className="inline-flex items-center gap-1.5 font-medium">
              <span className="h-3 w-3 rounded-[3px]" style={{ backgroundColor: color }} />
              {label}
            </span>
          ))}
        </div>
        <span className="text-[11px] text-slate-400">Hover any cell for exact hourly occupancy snapshot</span>
      </div>
    </div>
  );
}
