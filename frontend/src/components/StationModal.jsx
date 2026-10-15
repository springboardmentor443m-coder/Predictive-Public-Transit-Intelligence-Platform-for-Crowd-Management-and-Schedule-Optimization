import React from 'react';
import { X, MapPin, Building, AlertCircle, CheckCircle, Navigation, Send, Clock } from 'lucide-react';
import StatusBadge from './StatusBadge';

export default function StationModal({ station, onClose, onDispatchAlert, onSelectSchedule }) {
  if (!station) return null;

  const probs = station.probabilities || {
    Low: station.congestion_level === 'Low' ? 0.8 : 0.1,
    Medium: station.congestion_level === 'Medium' ? 0.75 : 0.15,
    High: station.congestion_level === 'High' ? 0.9 : 0.05,
  };

  const confidencePct = Math.round((station.confidence || 0.88) * 100);

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="ops-panel w-full max-w-lg overflow-hidden border border-slate-700 shadow-2xl animate-in fade-in zoom-in duration-150">
        {/* Header */}
        <div className="p-5 border-b border-slate-800 flex items-start justify-between bg-slate-900/80">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <StatusBadge status={station.congestion_level} />
              <span className="text-xs font-mono text-slate-400">
                ID: {station.id || 'ST-NYC'}
              </span>
            </div>
            <h3 className="text-lg font-bold text-white tracking-wide">
              {station.name || station['Stop Name']}
            </h3>
            <div className="flex items-center gap-3 text-xs text-slate-400 mt-1">
              <span className="flex items-center gap-1">
                <MapPin size={12} className="text-sky-400" />
                {station.borough || 'Manhattan'}
              </span>
              <span>•</span>
              <span className="flex items-center gap-1">
                <Building size={12} className="text-amber-400" />
                {station.structure || 'Subway'}
              </span>
              <span>•</span>
              <span className="font-mono text-slate-500">
                {station.latitude?.toFixed(4)}, {station.longitude?.toFixed(4)}
              </span>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X size={18} />
          </button>
        </div>

        {/* Content */}
        <div className="p-5 space-y-4 text-xs">
          {/* Operational Alert Box */}
          <div
            className={`p-3.5 rounded-lg border ${
              station.congestion_level === 'High'
                ? 'bg-rose-500/10 border-rose-500/30 text-rose-300'
                : station.congestion_level === 'Medium'
                ? 'bg-amber-500/10 border-amber-500/30 text-amber-300'
                : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
            }`}
          >
            <div className="font-semibold text-sm mb-1 flex items-center gap-1.5">
              <AlertCircle size={16} />
              <span>Operational Status & Directive</span>
            </div>
            <p className="text-slate-200 leading-relaxed">
              {station.alert_message || `Congestion level is ${station.congestion_level}.`}
            </p>
            <div className="mt-2 text-xs font-medium text-white/90">
              <strong>Action:</strong> {station.recommendation || 'Standard frequency is sufficient.'}
            </div>
          </div>

          {/* Model Confidence & Probabilities */}
          <div className="bg-slate-900/60 p-3.5 rounded-lg border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-slate-400 font-semibold uppercase tracking-wider text-[11px]">
                Model Classification Confidence
              </span>
              <span className="font-mono font-bold text-[#00D4AA] text-sm">
                {confidencePct}%
              </span>
            </div>

            {/* Probability Bars */}
            <div className="space-y-2 pt-1">
              {Object.entries(probs).map(([tier, prob]) => {
                const pct = Math.round(Number(prob) * 100);
                const color =
                  tier === 'High' ? '#EF4444' : tier === 'Medium' ? '#F59E0B' : '#10B981';
                return (
                  <div key={tier} className="space-y-1">
                    <div className="flex justify-between text-[11px]">
                      <span className="text-slate-400 font-medium">{tier} Congestion</span>
                      <span className="font-mono font-bold text-slate-300">{pct}%</span>
                    </div>
                    <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all duration-500"
                        style={{ width: `${pct}%`, backgroundColor: color }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="text-[11px] text-slate-500 italic bg-slate-900/30 p-2.5 rounded border border-slate-800/60">
            Note: Congestion tiers are derived from the trained Random Forest classifier based on spatial coordinates, temporal peak cycles, and station structural attributes.
          </div>
        </div>

        {/* Footer Actions */}
        <div className="p-4 bg-slate-900 border-t border-slate-800 flex items-center justify-end gap-2">
          {onSelectSchedule && (
            <button
              onClick={() => {
                onSelectSchedule(station.congestion_level);
                onClose();
              }}
              className="btn-secondary"
            >
              <Clock size={14} />
              <span>Adjust Headway</span>
            </button>
          )}

          {onDispatchAlert && (
            <button
              onClick={() => {
                onDispatchAlert(station);
                onClose();
              }}
              className="btn-primary"
            >
              <Send size={14} />
              <span>Dispatch Alert</span>
            </button>
          )}

          <button onClick={onClose} className="btn-secondary">
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
