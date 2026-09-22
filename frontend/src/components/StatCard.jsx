import React from 'react';

export default function StatCard({ title, value, subtitle, icon: Icon, color = "cyan", trend, badge }) {
  const colorMap = {
    cyan: {
      border: 'border-cyan-500/20 hover:border-cyan-500/40',
      iconBg: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20',
      glow: 'hover:shadow-cyan-500/10',
      text: 'text-cyan-400'
    },
    magenta: {
      border: 'border-pink-500/20 hover:border-pink-500/40',
      iconBg: 'bg-pink-500/10 text-pink-400 border-pink-500/20',
      glow: 'hover:shadow-pink-500/10',
      text: 'text-pink-400'
    },
    red: {
      border: 'border-red-500/20 hover:border-red-500/40',
      iconBg: 'bg-red-500/10 text-red-400 border-red-500/20',
      glow: 'hover:shadow-red-500/10',
      text: 'text-red-400'
    },
    yellow: {
      border: 'border-amber-500/20 hover:border-amber-500/40',
      iconBg: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
      glow: 'hover:shadow-amber-500/10',
      text: 'text-amber-400'
    },
    emerald: {
      border: 'border-emerald-500/20 hover:border-emerald-500/40',
      iconBg: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
      glow: 'hover:shadow-emerald-500/10',
      text: 'text-emerald-400'
    },
    indigo: {
      border: 'border-indigo-500/20 hover:border-indigo-500/40',
      iconBg: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20',
      glow: 'hover:shadow-indigo-500/10',
      text: 'text-indigo-400'
    }
  };

  const currentTheme = colorMap[color] || colorMap.cyan;

  return (
    <div className={`glass-panel rounded-2xl p-5 border ${currentTheme.border} transition-all duration-300 hover:-translate-y-1 hover:shadow-xl ${currentTheme.glow} relative overflow-hidden group`}>
      {/* Ambient background light */}
      <div className="absolute -right-6 -bottom-6 w-24 h-24 rounded-full bg-slate-800/40 pointer-events-none group-hover:scale-150 transition-transform duration-500"></div>

      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">{title}</p>
          <div className="flex items-baseline space-x-2 mt-2">
            <h3 className="text-2xl font-bold text-white font-display tracking-tight">{value}</h3>
            {badge && (
              <span className="text-[11px] font-mono font-medium px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                {badge}
              </span>
            )}
          </div>
          {subtitle && (
            <p className="text-xs text-slate-400 mt-1 flex items-center gap-1">
              {subtitle}
            </p>
          )}
        </div>

        {Icon && (
          <div className={`p-3 rounded-xl border ${currentTheme.iconBg} shadow-sm`}>
            <Icon className="w-5 h-5" />
          </div>
        )}
      </div>

      {trend && (
        <div className="mt-3 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
          <span>{trend.label}</span>
          <span className={`font-mono font-semibold ${trend.positive ? 'text-emerald-400' : 'text-amber-400'}`}>
            {trend.value}
          </span>
        </div>
      )}
    </div>
  );
}
