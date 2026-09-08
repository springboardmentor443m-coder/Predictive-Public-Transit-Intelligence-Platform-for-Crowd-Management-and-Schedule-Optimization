import React from 'react';
import { LucideIcon } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  trend?: string;
  trendPositive?: boolean;
  accentColor?: 'cyan' | 'amber' | 'emerald' | 'crimson';
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  trendPositive,
  accentColor = 'cyan',
}) => {
  const borderAccents = {
    cyan: 'border-l-metro-cyan hover:border-metro-cyan/70',
    amber: 'border-l-metro-amber hover:border-metro-amber/70',
    emerald: 'border-l-congestion-low hover:border-congestion-low/70',
    crimson: 'border-l-congestion-critical hover:border-congestion-critical/70',
  }[accentColor];

  const iconColors = {
    cyan: 'text-metro-cyan bg-cyan-950/40 border-cyan-800/40',
    amber: 'text-metro-amber bg-amber-950/40 border-amber-800/40',
    emerald: 'text-congestion-low bg-emerald-950/40 border-emerald-800/40',
    crimson: 'text-congestion-critical bg-red-950/40 border-red-800/40',
  }[accentColor];

  return (
    <div
      className={`bg-bg-card border border-border-dark border-l-4 rounded-xl p-5 shadow-card transition-all duration-300 hover:translate-y-[-2px] hover:shadow-glow ${borderAccents}`}
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-wider text-slate-400 font-mono">
            {title}
          </p>
          <h3 className="text-2xl font-bold font-mono text-slate-100 mt-1.5 tracking-tight">
            {value}
          </h3>
        </div>
        <div className={`p-3 rounded-lg border ${iconColors}`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>

      {(subtitle || trend) && (
        <div className="mt-3.5 pt-3 border-t border-border-subtle flex items-center justify-between text-xs">
          {subtitle && <span className="text-slate-400">{subtitle}</span>}
          {trend && (
            <span
              className={`font-mono font-semibold ${
                trendPositive ? 'text-emerald-400' : 'text-amber-400'
              }`}
            >
              {trend}
            </span>
          )}
        </div>
      )}
    </div>
  );
};
