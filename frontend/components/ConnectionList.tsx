import { MapPin, TrainFront, Footprints } from "lucide-react";
import { neighborsFor, type Neighbor } from "../lib/connections";
import { lineColor, lineInk, lineStyle } from "../lib/lines";
import type { Station, StationConnection } from "../lib/types";

interface ConnectionListProps {
  code?: string | null;
  connections?: StationConnection[];
  stations: Station[];
  onSelect?: (stationId: string) => void;
  className?: string;
}

interface RowProps {
  n: Neighbor;
  onSelect?: (stationId: string) => void;
}

function NeighborRow({ n, onSelect }: RowProps) {
  const name = n.name ?? n.code;
  const chip = (
    <button
      type="button"
      onClick={() => onSelect?.(n.code)}
      className="group w-full text-left"
      title={`${name} (${n.code}) · ${n.kind === "along_line" ? "directly on the tracks" : `${n.vias}`}`}
    >
      <div className="flex items-center gap-2 rounded-xl border border-slate-800 bg-slate-950/70 px-3 py-2 transition group-hover:border-brand-500/40 group-hover:bg-slate-900">
        <span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ backgroundColor: lineColor(n.line) }} />
        <span className="min-w-0 flex-1">
          <span className="block truncate text-xs font-bold text-white">{name}</span>
          <span className="block truncate text-[10px] font-mono text-slate-500">
            {n.code} · {n.kind === "along_line" ? n.vias.replace(/;/g, "/") : "walking interchange"}
          </span>
        </span>
        <span
          className="inline-flex shrink-0 items-center gap-1 rounded-md px-1.5 py-0.5 text-[10px] font-extrabold uppercase"
          style={{ color: lineInk(n.line ?? ""), backgroundColor: `${lineColor(n.line)}22` }}
        >
          {lineStyle(n.line).services || n.line}
        </span>
      </div>
    </button>
  );

  return (
    <li key={n.code} className={n.kind === "transfer" ? "relative" : undefined}>
      {chip}
    </li>
  );
}

export default function ConnectionList({ code, connections = [], stations, onSelect, className }: ConnectionListProps) {
  if (!code) return null;
  const neighbors = neighborsFor(code, connections, stations);
  const transferCount = neighbors.filter((n) => n.kind === "transfer").length;

  return (
    <div className={className}>
      <div className="flex items-center justify-between">
        <p className="text-[10px] font-extrabold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
          <MapPin className="h-3.5 w-3.5 text-brand-400" /> Connects To
        </p>
        <span className="text-[10px] font-mono text-slate-500">
          {neighbors.length} stop{neighbors.length === 1 ? "" : "s"}
          {transferCount > 0 ? ` · ${transferCount} walk` : ""}
        </span>
      </div>

      {neighbors.length === 0 ? (
        <p className="mt-2 rounded-xl border border-dashed border-slate-800 bg-slate-950/40 px-3 py-2.5 text-xs text-slate-500">
          No monitored stations are directly connected — the next real stop on this line isn&apos;t in the 59-station
          sample yet.
        </p>
      ) : (
        <ul className="mt-2.5 space-y-2">
          {neighbors.map((n) => (
            <NeighborRow key={n.code} n={n} onSelect={onSelect} />
          ))}
        </ul>
      )}

      <p className="mt-3 flex items-start gap-1.5 text-[10px] leading-relaxed text-slate-500">
        <Footprints className="mt-0.5 h-3 w-3 shrink-0" />
        Walking interchanges come from the MTA GTFS feed and the 42 St Shuttle / Queensboro Plaza same-complex
        corrections. Train links are consecutive monitored stops.
      </p>
    </div>
  );
}