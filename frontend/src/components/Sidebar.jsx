import React from 'react';
import {
  LayoutDashboard,
  Map,
  Train,
  Clock,
  AlertTriangle,
  Sparkles,
  TrendingUp,
  Database,
  Radio,
} from 'lucide-react';

const NAV_ITEMS = [
  { id: 'overview', label: 'Overview & Console', icon: LayoutDashboard, tag: 'OCC' },
  { id: 'crowd-monitoring', label: 'Crowd Monitoring (Map)', icon: Map, tag: 'GIS' },
  { id: 'train-tracking', label: 'Live Train Tracking', icon: Train, tag: 'SIM' },
  { id: 'schedule-management', label: 'Schedule Management', icon: Clock, tag: 'PLAN' },
  { id: 'alerts-center', label: 'Alerts & Incident Center', icon: AlertTriangle, tag: 'ALERTS' },
  { id: 'real-time-prediction', label: 'Real-Time Prediction', icon: Sparkles, tag: 'INFER' },
  { id: 'demand-forecasting', label: 'Demand Forecasting', icon: TrendingUp, tag: 'FORECAST' },
  { id: 'dataset-analytics', label: 'Dataset Analytics & EDA', icon: Database, tag: 'DATA' },
];

export default function Sidebar({ activeModule, onSelectModule, alertCount = 0 }) {
  return (
    <aside className="w-64 bg-[#111827] border-r border-slate-800 flex flex-col justify-between shrink-0 select-none">
      {/* Top Branding */}
      <div>
        <div className="h-16 px-5 border-b border-slate-800 flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-[#00D4AA] to-sky-600 flex items-center justify-center text-[#0B1220] font-black text-lg shadow-lg shadow-teal-500/20">
            M
          </div>
          <div>
            <div className="text-sm font-bold tracking-tight text-white flex items-center gap-1.5">
              <span>AI METROFLOW</span>
            </div>
            <div className="text-[10px] font-mono text-[#00D4AA] tracking-wider uppercase font-semibold">
              Transit Intel Platform
            </div>
          </div>
        </div>

        {/* Section Label */}
        <div className="px-5 pt-4 pb-2">
          <span className="text-[10px] font-bold tracking-widest text-slate-500 uppercase font-mono">
            Navigation Modules
          </span>
        </div>

        {/* Nav List */}
        <nav className="px-3 space-y-1">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = activeModule === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onSelectModule(item.id)}
                className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-medium transition-all ${
                  isActive
                    ? 'bg-slate-800 text-[#00D4AA] shadow-sm border border-slate-700/80 font-semibold'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon
                    size={16}
                    className={isActive ? 'text-[#00D4AA]' : 'text-slate-500'}
                  />
                  <span>{item.label}</span>
                </div>

                {item.id === 'alerts-center' && alertCount > 0 ? (
                  <span className="px-1.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30">
                    {alertCount}
                  </span>
                ) : (
                  <span
                    className={`text-[9px] font-mono px-1.5 py-0.5 rounded ${
                      isActive
                        ? 'bg-[#00D4AA]/10 text-[#00D4AA]'
                        : 'bg-slate-900 text-slate-600'
                    }`}
                  >
                    {item.tag}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Bottom Telemetry Card */}
      <div className="p-4 border-t border-slate-800/80 bg-slate-900/60 m-3 rounded-lg border">
        <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
          <span className="flex items-center gap-1.5 font-medium">
            <Radio size={12} className="text-[#00D4AA] animate-pulse" />
            <span>Sim Telemetry</span>
          </span>
          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 font-bold">
            READY
          </span>
        </div>
        <p className="text-[11px] text-slate-500 leading-relaxed">
          Predictive inference engine & subway kinematics runner active.
        </p>
      </div>
    </aside>
  );
}
