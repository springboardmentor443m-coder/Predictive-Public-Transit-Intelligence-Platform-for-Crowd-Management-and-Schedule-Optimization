import React, { useEffect, useState } from 'react';
import { 
  ShieldAlert, 
  AlertOctagon, 
  CheckCircle2, 
  Flame, 
  FileText, 
  Power,
  RotateCcw
} from 'lucide-react';

interface Incident {
  id: string;
  station_id: string;
  station_name: string;
  severity: string;
  type: string;
  density_pct: number;
  recommended_action: string;
  status: string;
  timestamp: string;
}

interface AuditLog {
  log_id: string;
  timestamp: string;
  station_name: string;
  action_taken: string;
  operator: string;
}

export const IncidentManager: React.FC = () => {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loadingAction, setLoadingAction] = useState<string | null>(null);

  const fetchIncidents = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/incidents/active');
      if (res.ok) {
        const data = await res.json();
        setIncidents(data.active_incidents || []);
        setLogs(data.audit_logs || []);
      }
    } catch (err) {
      console.error('Failed to load incident telemetry:', err);
    }
  };

  useEffect(() => {
    fetchIncidents();
  }, []);

  const handleMitigate = async (incident: Incident) => {
    setLoadingAction(incident.id);
    try {
      const res = await fetch('http://localhost:8000/api/incidents/execute-protocol', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          incident_id: incident.id,
          station_id: incident.station_name,
          action_type: incident.recommended_action
        })
      });

      if (res.ok) {
        await fetchIncidents();
      }
    } catch (err) {
      console.error('Protocol execution failed:', err);
    } finally {
      setLoadingAction(null);
    }
  };

  return (
    <div className="w-full bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 backdrop-blur-md">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-5 border-b border-slate-800/80 mb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <ShieldAlert className="w-4 h-4 text-rose-400" />
            <h2 className="text-sm font-bold tracking-wider uppercase text-slate-100">
              Surge Containment & Emergency Protocols
            </h2>
          </div>
          <p className="text-xs text-slate-400">
            Automated threshold violation responses and manual dispatcher overrides
          </p>
        </div>

        <button 
          onClick={fetchIncidents}
          className="flex items-center gap-1.5 text-xs font-mono text-slate-400 hover:text-slate-200 transition"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          Refresh Incident Log
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Active Emergency Protocol Cards */}
        <div className="lg:col-span-2 space-y-3.5">
          <span className="text-xs font-mono font-bold tracking-wider uppercase text-slate-400 block mb-2">
            Active Alerts Requiring Intervention
          </span>

          {incidents.filter(i => i.status !== 'MITIGATED').length === 0 ? (
            <div className="p-8 border border-slate-800/60 rounded-xl bg-slate-950/40 text-center font-mono text-xs text-emerald-400 flex items-center justify-center gap-2">
              <CheckCircle2 className="w-4 h-4" />
              NO CRITICAL SAFETY PROTOCOLS ACTIVE. NETWORK OPERATING WITHIN TOLERANCE.
            </div>
          ) : (
            incidents
              .filter(i => i.status !== 'MITIGATED')
              .map(inc => (
                <div
                  key={inc.id}
                  className="p-4 bg-slate-950/80 border border-rose-500/40 rounded-xl flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-[0_0_15px_rgba(244,63,94,0.06)]"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 rounded bg-rose-500/20 text-rose-400 font-mono text-[10px] font-bold">
                        {inc.id}
                      </span>
                      <span className="text-xs font-mono text-slate-400">{inc.timestamp}</span>
                      <span className="text-xs font-bold text-slate-200">• {inc.station_name}</span>
                    </div>
                    <div className="text-sm font-semibold text-rose-200 flex items-center gap-1.5">
                      <Flame className="w-4 h-4 text-rose-400 shrink-0" />
                      {inc.type.replace(/_/g, ' ')}
                    </div>
                    <p className="text-xs font-mono text-slate-400">
                      Density: <span className="text-rose-400 font-bold">{inc.density_pct}%</span> | Recommended: <span className="text-cyan-400">{inc.recommended_action.replace(/_/g, ' ')}</span>
                    </p>
                  </div>

                  <button
                    onClick={() => handleMitigate(inc)}
                    disabled={loadingAction === inc.id}
                    className="whitespace-nowrap px-4 py-2 bg-rose-500/20 hover:bg-rose-500/30 border border-rose-500/50 rounded-xl text-rose-300 font-mono text-xs font-bold transition flex items-center gap-2 self-start md:self-auto"
                  >
                    <Power className="w-3.5 h-3.5" />
                    {loadingAction === inc.id ? 'ENFORCING...' : 'ENFORCE PROTOCOL'}
                  </button>
                </div>
              ))
          )}
        </div>

        {/* Audit Log / History Sidebar */}
        <div className="bg-slate-950/70 border border-slate-800/80 rounded-xl p-4 flex flex-col">
          <span className="text-xs font-mono font-bold tracking-wider uppercase text-slate-400 block mb-3 flex items-center gap-1.5">
            <FileText className="w-3.5 h-3.5 text-cyan-400" /> Dispatch Audit Stream
          </span>

          <div className="space-y-2.5 flex-1 overflow-y-auto max-h-72">
            {logs.map((log) => (
              <div key={log.log_id} className="p-2.5 bg-slate-900/50 rounded-lg border border-slate-800/60 text-xs">
                <div className="flex items-center justify-between text-[10px] font-mono text-slate-500 mb-1">
                  <span>{log.log_id} • {log.timestamp}</span>
                  <span className="text-cyan-400">{log.operator}</span>
                </div>
                <div className="text-slate-300 font-medium">{log.action_taken}</div>
                <div className="text-[10px] text-slate-400 font-mono mt-0.5">Target: {log.station_name}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};