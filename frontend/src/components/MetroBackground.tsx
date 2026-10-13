import React from 'react';

export const MetroBackground: React.FC = () => {
  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none z-0">
      <div 
        className="absolute inset-0 opacity-15"
        style={{
          backgroundImage: `linear-gradient(to right, #1e293b 1px, transparent 1px),
                            linear-gradient(to bottom, #1e293b 1px, transparent 1px)`,
          backgroundSize: '40px 40px'
        }}
      />
      <svg className="w-full h-full opacity-40" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="cyanLine" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#06b6d4" stopOpacity="0.8" />
            <stop offset="100%" stopColor="#3b82f6" stopOpacity="0.2" />
          </linearGradient>
        </defs>
        <path
          d="M -100 250 L 350 250 L 550 500 L 1100 500 L 1300 750 L 2000 750"
          stroke="url(#cyanLine)"
          strokeWidth="3"
          fill="none"
          strokeDasharray="10 8"
        />
        <circle r="6" fill="#38bdf8">
          <animateMotion
            path="M -100 250 L 350 250 L 550 500 L 1100 500 L 1300 750 L 2000 750"
            dur="9s"
            repeatCount="indefinite"
          />
        </circle>
      </svg>
    </div>
  );
};