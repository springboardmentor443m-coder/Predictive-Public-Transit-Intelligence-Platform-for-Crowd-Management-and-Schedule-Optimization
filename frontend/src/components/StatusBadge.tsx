import React from 'react';
import { CongestionLabel } from '../types';

interface StatusBadgeProps {
  status: CongestionLabel | 'critical' | 'high' | 'medium' | 'low' | string;
  size?: 'sm' | 'md' | 'lg';
  showPulse?: boolean;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  size = 'md',
  showPulse = true,
}) => {
  const normStatus = status.toLowerCase();

  let colorClasses = 'bg-slate-800/80 text-slate-300 border-slate-700';
  let dotColor = 'bg-slate-400';
  let label = status.toUpperCase();

  if (normStatus === 'critical') {
    colorClasses = 'bg-[#3A0518]/80 text-[#FF3377] border-[#FF0055]/60 shadow-[0_0_14px_rgba(255,0,85,0.45)]';
    dotColor = 'bg-[#FF0055]';
    label = 'CRITICAL';
  } else if (normStatus === 'high') {
    colorClasses = 'bg-[#351E05]/80 text-[#FFB020] border-[#FF9E00]/60 shadow-[0_0_12px_rgba(255,158,0,0.35)]';
    dotColor = 'bg-[#FF9E00]';
    label = 'HIGH';
  } else if (normStatus === 'medium') {
    colorClasses = 'bg-[#042838]/80 text-[#38E1FF] border-[#00E5FF]/60 shadow-[0_0_10px_rgba(0,229,255,0.25)]';
    dotColor = 'bg-[#00E5FF]';
    label = 'MODERATE';
  } else if (normStatus === 'low') {
    colorClasses = 'bg-[#052E20]/80 text-[#34FFAE] border-[#05FFA1]/60 shadow-[0_0_10px_rgba(5,255,161,0.25)]';
    dotColor = 'bg-[#05FFA1]';
    label = 'OPTIMAL';
  }

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5 gap-1.5',
    md: 'text-xs px-2.5 py-1 gap-2',
    lg: 'text-sm px-3.5 py-1.5 gap-2.5 font-semibold',
  }[size];

  return (
    <span
      className={`inline-flex items-center font-mono uppercase tracking-wider font-semibold rounded-full border transition-all duration-300 ${colorClasses} ${sizeClasses}`}
    >
      <span className="relative flex h-2 w-2">
        {showPulse && normStatus === 'critical' && (
          <span className={`absolute inline-flex h-full w-full rounded-full opacity-75 animate-ping ${dotColor}`} />
        )}
        <span className={`relative inline-flex rounded-full h-2 w-2 ${dotColor}`} />
      </span>
      {label}
    </span>
  );
};
