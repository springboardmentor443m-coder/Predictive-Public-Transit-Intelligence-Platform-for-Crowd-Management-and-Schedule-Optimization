import React from 'react';

export default function MetricCard({
  title,
  value,
  subtext,
  delta,
  deltaType = 'neutral', // 'positive' | 'negative' | 'neutral' | 'warning'
  icon: Icon,
  accentColor = '#00D4AA',
  className = '',
}) {
  return (
    <div
      className={`ops-card p-4 relative overflow-hidden flex flex-col justify-between ${className}`}
      style={{
        borderLeft: `4px solid ${accentColor}`,
        background: 'linear-gradient(135deg, rgba(31, 41, 61, 0.95) 0%, rgba(17, 24, 39, 0.95) 100%)',
      }}
    >
      <div className="flex items-start justify-between">
        <span className="text-xs font-semibold tracking-wider uppercase text-slate-400">
          {title}
        </span>
        {Icon && (
          <div
            className="p-2 rounded-lg"
            style={{
              backgroundColor: `${accentColor}18`,
              color: accentColor,
            }}
          >
            <Icon size={18} />
          </div>
        )}
      </div>

      <div className="mt-2">
        <div className="text-2xl font-bold font-mono text-slate-100 tracking-tight">
          {value}
        </div>

        {(delta || subtext) && (
          <div className="mt-1 flex items-center gap-1.5 text-xs text-slate-400">
            {delta && (
              <span
                className={`font-semibold ${
                  deltaType === 'positive'
                    ? 'text-emerald-400'
                    : deltaType === 'warning'
                    ? 'text-amber-400'
                    : deltaType === 'negative'
                    ? 'text-rose-400'
                    : 'text-sky-400'
                }`}
              >
                {delta}
              </span>
            )}
            {subtext && <span>{subtext}</span>}
          </div>
        )}
      </div>
    </div>
  );
}
