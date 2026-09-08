import React from 'react';
import { NavLink } from 'react-router-dom';
import { Map, Calendar, AlertTriangle, BarChart3, Radio, Sparkles } from 'lucide-react';

const NAV_ITEMS = [
  { path: '/', label: 'Live Network Map', icon: Map },
  { path: '/schedule', label: 'Train Scheduling', icon: Calendar },
  { path: '/alerts', label: 'Alerts & Incidents', icon: AlertTriangle },
  { path: '/analytics', label: 'Analytics & Heatmaps', icon: BarChart3 },
];

export const Sidebar: React.FC = () => {
  return (
    <aside className="w-64 bg-bg-surface border-r border-border-dark flex flex-col justify-between p-4 shrink-0 min-h-[calc(100vh-4rem)]">
      {/* Navigation Links */}
      <div className="space-y-2">
        <p className="px-3 text-[11px] font-mono font-bold uppercase tracking-wider text-slate-500 mb-2">
          Control Center
        </p>
        {NAV_ITEMS.map(({ path, label, icon: Icon }) => (
          <NavLink
            key={path}
            to={path}
            end={path === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all duration-300 ${
                isActive
                  ? 'bg-gradient-to-r from-metro-primary/20 to-metro-cyan/15 text-white border border-metro-primary/50 shadow-[0_0_20px_rgba(168,85,247,0.3)] font-bold'
                  : 'text-slate-400 hover:text-slate-100 hover:bg-bg-card hover:border hover:border-border-dark/60'
              }`
            }
          >
            <Icon className="w-4 h-4 text-[#00F5D4]" />
            <span>{label}</span>
          </NavLink>
        ))}
      </div>

      {/* Network Status Widget */}
      <div className="bg-bg-card/90 border border-border-dark rounded-2xl p-4 text-xs font-mono shadow-card">
        <div className="flex items-center justify-between mb-2.5 pb-2 border-b border-border-dark/60">
          <span className="text-slate-400 font-semibold">AI ENGINE</span>
          <span className="text-[#05FFA1] flex items-center gap-1 font-bold">
            <Radio className="w-3 h-3 animate-pulse text-[#05FFA1]" /> LIVE INFERENCE
          </span>
        </div>
        <div className="space-y-2 text-slate-400 text-[11px]">
          <div className="flex justify-between">
            <span>Model Artifact:</span>
            <span className="text-slate-200 font-semibold">RandomForest (11 Feat)</span>
          </div>
          <div className="flex justify-between">
            <span>Cache Tier:</span>
            <span className="text-[#00F5D4] font-semibold">Redis 300s TTL</span>
          </div>
          <div className="flex justify-between">
            <span>Network Grid:</span>
            <span className="text-slate-200 font-semibold">Seoul Lines 1-9</span>
          </div>
        </div>
      </div>
    </aside>
  );
};
