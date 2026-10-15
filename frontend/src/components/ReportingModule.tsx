import React, { useEffect, useState } from 'react';
import { 
  FileDown, 
  Settings2, 
  BarChart3, 
  Sliders, 
  Save, 
  Check, 
  Clock, 
  ShieldCheck 
} from 'lucide-react';

interface CorridorData {
  name: string;
  volume: number;
  avg_load_pct: number;
}

interface ReportData {
  weekly_footfall: number;
  on_time_dispatch_rate_pct: number;
  bottlenecks_mitigated: number;
  peak_hour: string;
  corridor_breakdown: CorridorData[];
  settings: {
    normal_threshold_pct: number;
    elevated_threshold_pct: number;
    auto_dispatch_enabled: boolean;
  };
}

export const ReportingModule: React.FC = () => {
  const [report, setReport] = useState<ReportData | null>(null);
  const [normalThresh, setNormalThresh] = useState<number>(60);
  const [elevatedThresh, setElevatedThresh] = useState<number>(80);
  const [autoDispatch, setAutoDispatch] = useState<boolean>(true);
  const [savedStatus, setSavedStatus] = useState<boolean>(false);

  const fetchReports = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/reports/summary');
      if (res.ok) {
        const data = await res.json();
        setReport(data);
        setNormalThresh(data.settings.normal_threshold_pct);
        setElevatedThresh(data.settings.elevated_threshold_pct);
        setAutoDispatch(data.settings.auto_dispatch_enabled);
      }
    } catch (err) {
      console.error('Reports fetch failed:', err);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  const handleSaveSettings = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/reports/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          normal_threshold_pct: Number(normalThresh),
          elevated_threshold_pct: Number(elevatedThresh),
          auto_dispatch_enabled: autoDispatch
        })
      });
      if (res.ok) {
        setSavedStatus(true);
        setTimeout(() => setSavedStatus(false), 3000);
      }
    } catch (err) {
      console.error('Failed to update settings:', err);
    }
  };

  const handleDownloadCsv = () => {
    window.open('http://localhost:8000/api/reports/export/csv', '_blank');
  };

  if (!report) return null;

  return (
    <div className="w-full bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 backdrop-blur-md">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-5 border-b border-slate-800/80 mb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <BarChart3 className="w-4 h-4 text-cyan-400" />
            <h2 className="text-sm font-bold tracking-wider uppercase text-slate-100">
              Audit Telemetry, Reporting & Control Parameters
            </h2>
          </div>
          <p className="text-xs text-slate-400">
            Historical passenger volume trends, CSV export, and live safety threshold controls
          </p>
        </div>

        <button
          onClick={handleDownloadCsv}
          className="flex items-center gap-2 px-4 py-2 bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/40 text-cyan-300 rounded-xl font-mono text-xs font-semibold transition"
        >
          <FileDown className="w-4 h-4" />
          Export Audit Telemetry (CSV)
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Performance Metrics Breakdown */}
        <div className="lg:col-span-2 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="p-3.5 bg-slate-950/70 border border-slate-800/70 rounded-xl">
              <span className="text-[10px] font-mono text-slate-500 block uppercase">Weekly Network Footfall</span>
              <span className="text-lg font-bold font-mono text-slate-100 mt-1 block">
                {report.weekly_footfall.toLocaleString()}
              </span>
            </div>
            <div className="p-3.5 bg-slate-950/70 border border-slate-800/70 rounded-xl">
              <span className="text-[10px] font-mono text-slate-500 block uppercase">Dispatch Adherence</span>
              <span className="text-lg font-bold font-mono text-emerald-400 mt-1 block flex items-center gap-1">
                <ShieldCheck className="w-4 h-4" />
                {report.on_time_dispatch_rate_pct}%
              </span>
            </div>
            <div className="p-3.5 bg-slate-950/70 border border-slate-800/70 rounded-xl">
              <span className="text-[10px] font-mono text-slate-500 block uppercase">Bottlenecks Mitigated</span>
              <span className="text-lg font-bold font-mono text-cyan-400 mt-1 block">
                {report.bottlenecks_mitigated} Active Loops
              </span>
            </div>
          </div>

          {/* Corridor Throughput Bars */}
          <div className="p-4 bg-slate-950/70 border border-slate-800/70 rounded-xl space-y-3">
            <span className="text-xs font-mono text-slate-400 uppercase tracking-wide block">
              Corridor Historical Passenger Volume
            </span>
            {report.corridor_breakdown.map((corridor) => (
              <div key={corridor.name} className="space-y-1">
                <div className="flex justify-between text-xs font-mono">
                  <span className="text-slate-300 font-semibold">{corridor.name}</span>
                  <span className="text-slate-400">{corridor.volume.toLocaleString()} passengers ({corridor.avg_load_pct}% avg load)</span>
                </div>
                <div className="w-full bg-slate-900 h-2 rounded-full overflow-hidden border border-slate-800">
                  <div 
                    className="bg-cyan-500 h-full rounded-full" 
                    style={{ width: `${corridor.avg_load_pct}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Dynamic Parameter Settings Panel */}
        <div className="bg-slate-950/80 border border-slate-800/80 rounded-xl p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 mb-4 pb-2 border-b border-slate-800">
              <Settings2 className="w-4 h-4 text-cyan-400" />
              <h3 className="text-xs font-mono font-bold uppercase text-slate-200">
                System Threshold Controls
              </h3>
            </div>

            <div className="space-y-4">
              <div>
                <label className="text-xs font-mono text-slate-400 block mb-1">
                  Normal Threshold Limit (&lt; %)
                </label>
                <input
                  type="number"
                  value={normalThresh}
                  onChange={(e) => setNormalThresh(Number(e.target.value))}
                  className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs font-mono text-emerald-400 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="text-xs font-mono text-slate-400 block mb-1">
                  Congestion Alert Trigger (&gt; %)
                </label>
                <input
                  type="number"
                  value={elevatedThresh}
                  onChange={(e) => setElevatedThresh(Number(e.target.value))}
                  className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5 text-xs font-mono text-rose-400 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div className="pt-2 flex items-center justify-between">
                <span className="text-xs font-mono text-slate-400">Autonomous Fleet Dispatch</span>
                <input
                  type="checkbox"
                  checked={autoDispatch}
                  onChange={(e) => setAutoDispatch(e.target.checked)}
                  className="w-4 h-4 accent-cyan-500 cursor-pointer"
                />
              </div>
            </div>
          </div>

          <button
            onClick={handleSaveSettings}
            className="w-full mt-5 py-2 px-3 bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-bold rounded-xl text-xs font-mono flex items-center justify-center gap-2 transition"
          >
            {savedStatus ? <Check className="w-4 h-4 text-slate-950" /> : <Save className="w-4 h-4" />}
            {savedStatus ? 'THRESHOLDS UPDATED' : 'SAVE THRESHOLDS'}
          </button>
        </div>
      </div>
    </div>
  );
};