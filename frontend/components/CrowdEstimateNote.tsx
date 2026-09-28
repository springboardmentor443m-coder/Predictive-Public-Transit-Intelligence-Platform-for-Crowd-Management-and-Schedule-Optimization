import type { LiveCrowdSnapshot } from "../lib/types";

function formatBucketStart(iso?: string): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleTimeString(undefined, {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}

function clampPct(v?: number): number | null {
  if (typeof v !== "number" || Number.isNaN(v)) return null;
  return Math.round(Math.min(100, Math.max(0, v)));
}

export default function CrowdEstimateNote({
  snapshot,
}: {
  snapshot: LiveCrowdSnapshot | null | undefined;
}) {
  if (!snapshot) return null;
  if (snapshot.is_estimate) {
    const pct = clampPct(snapshot.hour_elapsed_pct);
    const bucket = formatBucketStart(snapshot.bucket_start);
    return (
      <p className="mt-1.5 text-[10px] font-medium text-amber-300/80">
        Estimated from hourly bucket
        {bucket ? ` · ${bucket}` : ""}
        {pct !== null ? ` · ${pct}% through the hour` : ""}
      </p>
    );
  }
  return <p className="mt-1.5 text-[10px] font-medium text-slate-500">Live reading</p>;
}