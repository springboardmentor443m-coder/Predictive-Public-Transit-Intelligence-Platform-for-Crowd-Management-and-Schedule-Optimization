import React from 'react';

interface RouteFilterProps {
  selectedRoute: string;
  onSelectRoute: (route: string) => void;
}

const SUBWAY_ROUTES = [
  { id: '', label: 'All Lines' },
  { id: '1', label: '1 Line', color: 'bg-red-600' },
  { id: '2', label: '2 Line', color: 'bg-red-600' },
  { id: '3', label: '3 Line', color: 'bg-red-600' },
  { id: '4', label: '4 Line', color: 'bg-emerald-600' },
  { id: '5', label: '5 Line', color: 'bg-emerald-600' },
  { id: '6', label: '6 Line', color: 'bg-emerald-600' },
  { id: '7', label: '7 Line', color: 'bg-purple-600' },
  { id: 'A', label: 'A Line', color: 'bg-blue-600' },
  { id: 'C', label: 'C Line', color: 'bg-blue-600' },
  { id: 'E', label: 'E Line', color: 'bg-blue-600' },
  { id: 'N', label: 'N Line', color: 'bg-amber-500 text-black' },
  { id: 'Q', label: 'Q Line', color: 'bg-amber-500 text-black' },
  { id: 'R', label: 'R Line', color: 'bg-amber-500 text-black' },
  { id: 'W', label: 'W Line', color: 'bg-amber-500 text-black' },
  { id: 'B', label: 'B Line', color: 'bg-orange-500' },
  { id: 'D', label: 'D Line', color: 'bg-orange-500' },
  { id: 'F', label: 'F Line', color: 'bg-orange-500' },
  { id: 'M', label: 'M Line', color: 'bg-orange-500' },
  { id: 'L', label: 'L Line', color: 'bg-slate-500' },
  { id: 'G', label: 'G Line', color: 'bg-lime-600' },
  { id: 'SI', label: 'SIR Line', color: 'bg-sky-700' },
];

export const RouteFilter: React.FC<RouteFilterProps> = ({
  selectedRoute,
  onSelectRoute,
}) => {
  return (
    <div className="flex items-center gap-1.5 overflow-x-auto pb-2 scrollbar-thin scrollbar-thumb-slate-800">
      {SUBWAY_ROUTES.map((route) => {
        const isSelected = selectedRoute === route.id;
        return (
          <button
            key={route.id}
            onClick={() => onSelectRoute(route.id)}
            className={`px-3 py-1.5 rounded-lg text-xs font-mono font-semibold transition-all whitespace-nowrap flex items-center gap-1.5 border ${
              isSelected
                ? 'bg-cyan-950 text-cyan-300 border-cyan-500 shadow-md shadow-cyan-950/40'
                : 'bg-slate-900/80 text-slate-400 hover:text-slate-200 border-slate-800 hover:border-slate-700'
            }`}
          >
            {route.id && (
              <span
                className={`w-4 h-4 rounded-full flex items-center justify-center text-[10px] font-bold ${
                  route.color || 'bg-slate-700 text-white'
                }`}
              >
                {route.id}
              </span>
            )}
            <span>{route.label}</span>
          </button>
        );
      })}
    </div>
  );
};
