import React from 'react';

export default function StatusBadge({ status, type, size = 'md' }) {
  const norm = (status || type || '').toString().toLowerCase().trim();

  let badgeClass = 'badge-info';
  let dotColor = '#38BDF8';
  let isPulse = false;

  if (norm.includes('high') || norm.includes('critical') || norm.includes('delayed')) {
    badgeClass = 'badge-high';
    dotColor = '#EF4444';
    isPulse = true;
  } else if (norm.includes('med') || norm.includes('warning') || norm.includes('arriving')) {
    badgeClass = 'badge-medium';
    dotColor = '#F59E0B';
  } else if (norm.includes('low') || norm.includes('normal') || norm.includes('time') || norm.includes('healthy')) {
    badgeClass = 'badge-low';
    dotColor = '#10B981';
  } else if (norm.includes('sim')) {
    badgeClass = 'badge-simulated';
    dotColor = '#818CF8';
  }

  const padding = size === 'sm' ? 'px-2 py-0.5 text-[11px]' : 'px-2.5 py-1 text-xs';

  return (
    <span className={`badge ${badgeClass} ${padding}`}>
      <span
        className={`status-dot ${isPulse ? 'pulse' : ''}`}
        style={{ backgroundColor: dotColor }}
      />
      {status}
    </span>
  );
}
