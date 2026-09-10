import React from 'react';
import { PRESETS } from '../data/constants';
import { Sparkles, ArrowRight, Zap } from 'lucide-react';

export default function QuickPresets({ onSelectPreset, activePresetIndex }) {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Sparkles className="w-4 h-4 text-amber-400 animate-spin-slow" />
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 font-mono">
            1-Click Simulation Scenarios
          </h4>
        </div>
        <span className="text-[11px] text-slate-500 font-mono">
          Pre-configured Network Peaks
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {PRESETS.map((p, idx) => {
          const isSelected = activePresetIndex === idx;
          return (
            <button
              key={idx}
              onClick={() => onSelectPreset(p, idx)}
              className={`p-3.5 rounded-xl text-left border transition-all duration-200 relative group overflow-hidden ${
                isSelected
                  ? 'bg-cyan-950/40 border-cyan-400/80 shadow-md shadow-cyan-500/10 ring-1 ring-cyan-400'
                  : 'bg-slate-900/60 border-slate-800 hover:border-slate-700 hover:bg-slate-800/40'
              }`}
            >
              <div className="flex items-start justify-between">
                <span className={`px-2 py-0.5 text-[10px] font-bold uppercase font-mono rounded border ${p.badgeColor}`}>
                  {p.expected_tier === 'SEVERE_RUSH' ? '🔴 Rush' : (p.expected_tier === 'MODERATE_TRAFFIC' ? '🟡 Midday' : '🟢 Off-Peak')}
                </span>
                <span className="text-[11px] font-mono text-slate-400">
                  {p.hour.toString().padStart(2, '0')}:00
                </span>
              </div>

              <h5 className="text-xs font-bold text-slate-100 mt-2 group-hover:text-cyan-300 transition-colors">
                {p.title}
              </h5>
              <p className="text-[11px] text-slate-400 mt-1 line-clamp-2 leading-relaxed">
                {p.desc}
              </p>

              <div className="mt-2.5 pt-2 border-t border-slate-800/80 flex items-center justify-between text-[10px] font-mono text-cyan-400/90">
                <span className="flex items-center gap-1">
                  <Zap className="w-3 h-3 text-cyan-400" />
                  Simulate
                </span>
                <ArrowRight className="w-3 h-3 group-hover:translate-x-1 transition-transform" />
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
