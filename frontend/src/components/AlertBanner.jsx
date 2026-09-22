import React from 'react';
import { ShieldAlert, AlertTriangle, CheckCircle2, Radio, BellRing, ArrowRight, Zap } from 'lucide-react';

export default function AlertBanner({ alertStatus, fleetAction, headway }) {
  if (!alertStatus) return null;

  const isEmergency = alertStatus.is_emergency || alertStatus.alert_level === "CRITICAL_OVERCROWDING";
  const isModerate = alertStatus.tier === "MODERATE_TRAFFIC" || alertStatus.alert_level === "MODERATE_CONGESTION";

  return (
    <div className={`rounded-2xl p-5 border transition-all duration-300 relative overflow-hidden ${
      isEmergency 
        ? 'bg-red-950/40 border-red-500/50 shadow-lg shadow-red-500/10' 
        : (isModerate 
            ? 'bg-amber-950/30 border-amber-500/40 shadow-lg shadow-amber-500/10' 
            : 'bg-emerald-950/30 border-emerald-500/30 shadow-lg shadow-emerald-500/10')
    }`}>
      {/* Dynamic top edge glow */}
      <div className={`absolute top-0 left-0 right-0 h-1 ${
        isEmergency ? 'bg-red-500 animate-pulse' : (isModerate ? 'bg-amber-500' : 'bg-emerald-500')
      }`}></div>

      <div className="flex items-start space-x-3.5">
        <div className={`p-2.5 rounded-xl border flex-shrink-0 ${
          isEmergency 
            ? 'bg-red-500/20 text-red-400 border-red-500/40 animate-bounce' 
            : (isModerate 
                ? 'bg-amber-500/20 text-amber-400 border-amber-500/30' 
                : 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30')
        }`}>
          {isEmergency ? (
            <ShieldAlert className="w-5 h-5" />
          ) : isModerate ? (
            <AlertTriangle className="w-5 h-5" />
          ) : (
            <CheckCircle2 className="w-5 h-5" />
          )}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div className="flex items-center space-x-2">
              <span className={`text-xs font-black uppercase font-mono px-2 py-0.5 rounded border ${
                isEmergency 
                  ? 'bg-red-500 text-white border-red-400' 
                  : (isModerate 
                      ? 'bg-amber-500/30 text-amber-300 border-amber-500/50' 
                      : 'bg-emerald-500/30 text-emerald-300 border-emerald-500/50')
              }`}>
                {alertStatus.alert_level || 'OPERATIONAL ALERT'}
              </span>
              <span className="text-xs text-slate-400 font-mono">
                Real-Time Rule Engine
              </span>
            </div>

            <div className="flex items-center space-x-1.5 text-[11px] font-mono text-cyan-300 bg-cyan-950/60 px-2.5 py-1 rounded-lg border border-cyan-800/60">
              <Zap className="w-3 h-3 text-cyan-400" />
              <span>Headway: {headway || alertStatus.recommended_headway_min || 3} min</span>
            </div>
          </div>

          <p className="text-sm font-semibold text-slate-100 mt-2">
            {alertStatus.message}
          </p>

          {/* Action Directive Callout */}
          <div className="mt-3 p-3 rounded-xl bg-slate-900/90 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <p className="text-[10px] uppercase tracking-wider text-slate-400 font-mono font-bold">
                Automated Fleet Action Directive
              </p>
              <p className="text-xs font-bold text-white mt-0.5">
                {fleetAction || alertStatus.recommended_action || "Maintain Standard Headway"}
              </p>
            </div>

            <div className="flex items-center space-x-1.5 flex-wrap">
              {(alertStatus.channels_notified || ["OCC WebSockets", "Platform Signage", "PA Audio"]).map((ch, idx) => (
                <span key={idx} className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700/60 flex items-center gap-1">
                  <Radio className="w-2.5 h-2.5 text-cyan-400" />
                  {ch}
                </span>
              ))}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
