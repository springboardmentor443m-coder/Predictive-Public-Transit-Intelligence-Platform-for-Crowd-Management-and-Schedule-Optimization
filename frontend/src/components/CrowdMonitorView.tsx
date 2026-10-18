import React, { useState } from 'react';
import { Users, AlertTriangle, Train, ArrowDownRight, ArrowUpRight, Search, MapPin, Zap } from 'lucide-react';
import { NetworkSnapshot, HorizonPrediction } from '../types';
import { LiveMap } from './LiveMap';

interface CrowdMonitorViewProps {
  snapshot: NetworkSnapshot | null;
  predictedStations: HorizonPrediction[] | null;
  activeHorizon: number;
  onSelectStation: (stationId: string) => void;
  onOpenAlerts: () => void;
}

export const CrowdMonitorView: React.FC<CrowdMonitorViewProps> = ({
  snapshot,
  predictedStations,
  activeHorizon,
  onSelectStation,
  onOpenAlerts
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [boroughFilter, setBoroughFilter] = useState('ALL');

  if (!snapshot) {
    return (
      <div className="p-12 text-center text-slate-400 animate-pulse">
        Connecting to live NYC transit telemetry stream...
      </div>
    );
  }

  const { network_metrics, stations, trains } = snapshot;

  const filteredStations = stations.filter(s => {
    const matchesSearch = s.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          s.lines.some(l => l.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesBorough = boroughFilter === 'ALL' || s.borough.toLowerCase() === boroughFilter.toLowerCase();
    return matchesSearch && matchesBorough;
  });

  // Top congested stations
  const topCongested = [...stations].sort((a, b) => b.density_percent - a.density_percent).slice(0, 5);

  return (
    <div className="space-y-6">
      {/* Network KPI Cards Bar */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3.5">
        <div className="bg-slate-900 border border-slate-800 p-3.5 rounded-2xl shadow-sm">
          <div className="flex items-center space-x-2 text-slate-400 text-xs mb-1">
            <Users className="w-3.5 h-3.5 text-blue-400" />
            <span className="truncate">Active Passengers</span>
          </div>
          <div className="text-xl font-black text-white">
            {network_metrics.active_network_passengers.toLocaleString()}
          </div>
          <div className="text-[10px] text-slate-400 mt-1">
            Across 20 Primary Stations
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-3.5 rounded-2xl shadow-sm">
          <div className="flex items-center space-x-2 text-slate-400 text-xs mb-1">
            <Zap className="w-3.5 h-3.5 text-amber-400" />
            <span className="truncate">Network Density</span>
          </div>
          <div className="text-xl font-black text-amber-400">
            {network_metrics.overall_density_percent}%
          </div>
          <div className="w-full bg-slate-800 h-1.5 rounded-full mt-2 overflow-hidden">
            <div
              className="bg-amber-400 h-full rounded-full transition-all duration-500"
              style={{ width: `${network_metrics.overall_density_percent}%` }}
            ></div>
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-3.5 rounded-2xl shadow-sm">
          <div className="flex items-center space-x-2 text-slate-400 text-xs mb-1">
            <AlertTriangle className="w-3.5 h-3.5 text-red-400" />
            <span className="truncate">Bottleneck Hubs</span>
          </div>
          <div className="text-xl font-black text-red-400">
            {network_metrics.severe_congestion_stations + network_metrics.high_congestion_stations}
          </div>
          <div className="text-[10px] text-slate-400 mt-1">
            {network_metrics.severe_congestion_stations} Severe &bull; {network_metrics.high_congestion_stations} High
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-3.5 rounded-2xl shadow-sm">
          <div className="flex items-center space-x-2 text-slate-400 text-xs mb-1">
            <Train className="w-3.5 h-3.5 text-emerald-400" />
            <span className="truncate">Active Trains</span>
          </div>
          <div className="text-xl font-black text-emerald-400">
            {trains.length}
          </div>
          <div className="text-[10px] text-slate-400 mt-1">
            Simulated GPS Positioning
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-3.5 rounded-2xl shadow-sm">
          <div className="flex items-center space-x-2 text-slate-400 text-xs mb-1">
            <ArrowDownRight className="w-3.5 h-3.5 text-cyan-400" />
            <span className="truncate">Turnstile Inflow</span>
          </div>
          <div className="text-xl font-black text-cyan-400">
            {network_metrics.total_inflow_rate.toLocaleString()}
          </div>
          <div className="text-[10px] text-slate-400 mt-1">
            passengers / min entry
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-3.5 rounded-2xl shadow-sm">
          <div className="flex items-center space-x-2 text-slate-400 text-xs mb-1">
            <ArrowUpRight className="w-3.5 h-3.5 text-purple-400" />
            <span className="truncate">Turnstile Outflow</span>
          </div>
          <div className="text-xl font-black text-purple-400">
            {network_metrics.total_outflow_rate.toLocaleString()}
          </div>
          <div className="text-[10px] text-slate-400 mt-1">
            passengers / min exit
          </div>
        </div>
      </div>

      {/* Main Command Center: Live Map & Sidebar */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Interactive Map Column (3 spans) */}
        <div className="lg:col-span-3 space-y-4">
          <LiveMap
            stations={stations}
            trains={trains}
            predictedStations={predictedStations}
            activeHorizon={activeHorizon}
            onSelectStation={onSelectStation}
          />
        </div>

        {/* Real-time Station Flow Feed (1 span) */}
        <div className="space-y-4 flex flex-col">
          {/* Station Search & Filter */}
          <div className="bg-slate-900 border border-slate-800 p-4 rounded-2xl space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-white flex items-center space-x-2">
                <MapPin className="w-4 h-4 text-blue-400" />
                <span>Station Monitoring</span>
              </h3>
              <span className="text-[11px] text-slate-400 font-mono">{stations.length} Tracked</span>
            </div>

            <div className="relative">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                value={searchTerm}
                onChange={e => setSearchTerm(e.target.value)}
                placeholder="Search station or line (e.g. 1, 4, Times Sq)..."
                className="w-full pl-9 pr-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
              />
            </div>

            <div className="flex space-x-1.5 text-[11px]">
              {['ALL', 'Manhattan', 'Brooklyn', 'Queens'].map(b => (
                <button
                  key={b}
                  onClick={() => setBoroughFilter(b)}
                  className={`px-2.5 py-1 rounded-lg font-semibold transition cursor-pointer ${
                    boroughFilter === b
                      ? 'bg-blue-600 text-white'
                      : 'bg-slate-950 text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {b}
                </button>
              ))}
            </div>

            {/* Station List */}
            <div className="space-y-2 max-h-[380px] overflow-y-auto pr-1">
              {filteredStations.map(s => {
                const isSevere = s.density_percent >= 85;
                const isHigh = s.density_percent >= 70;
                const isModerate = s.density_percent >= 45;

                return (
                  <div
                    key={s.id}
                    onClick={() => onSelectStation(s.id)}
                    className="p-3 bg-slate-950/80 hover:bg-slate-800/80 border border-slate-800 hover:border-slate-700 rounded-xl transition cursor-pointer flex items-center justify-between"
                  >
                    <div>
                      <div className="text-xs font-bold text-white flex items-center space-x-1.5">
                        <span className="truncate max-w-[140px]">{s.name}</span>
                        <span className="text-[10px] text-slate-400 font-normal">({s.lines.join(',')})</span>
                      </div>
                      <div className="text-[10px] text-slate-400 mt-0.5">
                        Inflow: <span className="text-emerald-400 font-semibold">{s.inflow_rate}</span> &bull; Occ: {s.current_occupancy.toLocaleString()}
                      </div>
                    </div>

                    <div className="text-right">
                      <div className={`text-xs font-black ${
                        isSevere ? 'text-red-400' : isHigh ? 'text-orange-400' : isModerate ? 'text-amber-400' : 'text-emerald-400'
                      }`}>
                        {s.density_percent}%
                      </div>
                      <span className={`text-[9px] font-bold uppercase px-1.5 py-0.2 rounded ${
                        isSevere ? 'bg-red-500/20 text-red-300' : isHigh ? 'bg-orange-500/20 text-orange-300' : isModerate ? 'bg-amber-500/20 text-amber-300' : 'bg-emerald-500/20 text-emerald-300'
                      }`}>
                        {s.congestion_level}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Quick Critical Alert Banner */}
          {network_metrics.severe_congestion_stations > 0 && (
            <div
              onClick={onOpenAlerts}
              className="p-4 bg-red-950/40 border border-red-500/50 rounded-2xl text-xs text-red-200 flex items-center justify-between cursor-pointer hover:bg-red-950/60 transition shadow-lg shadow-red-950/30"
            >
              <div className="flex items-center space-x-2.5">
                <AlertTriangle className="w-4 h-4 text-red-400 animate-pulse flex-shrink-0" />
                <div>
                  <div className="font-bold text-red-300">Overcrowding Advisory Active</div>
                  <div className="text-[11px] text-red-400">Headway adjustments recommended</div>
                </div>
              </div>
              <span className="text-xs font-bold text-red-400">&rarr;</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
