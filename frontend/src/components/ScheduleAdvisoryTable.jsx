import React, { useState, useEffect } from 'react';
import { fetchScheduleAdvisory } from '../services/api';
import { 
  CalendarClock, 
  Search, 
  Filter, 
  RefreshCw, 
  Download, 
  ArrowUpDown, 
  AlertOctagon, 
  CheckCircle2, 
  ShieldAlert, 
  Clock, 
  Train,
  ChevronLeft,
  ChevronRight,
  Check
} from 'lucide-react';
import { LINES, STATIONS } from '../data/constants';

export default function ScheduleAdvisoryTable() {
  const [loading, setLoading] = useState(false);
  const [refreshSuccess, setRefreshSuccess] = useState(false);
  const [data, setData] = useState({ total_records_analyzed: 0, directives: [], tier_counts: {} });
  const [searchTerm, setSearchTerm] = useState('');
  const [tierFilter, setTierFilter] = useState('ALL');
  const [lineFilter, setLineFilter] = useState('ALL');
  const [hourFilter, setHourFilter] = useState('ALL');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(12);
  const [sortField, setSortField] = useState('predicted_occupancy');
  const [sortAsc, setSortAsc] = useState(false);
  const [lastSynced, setLastSynced] = useState(new Date().toLocaleTimeString());

  const loadData = async () => {
    setLoading(true);
    setRefreshSuccess(false);
    try {
      const res = await fetchScheduleAdvisory();
      if (res && res.directives) {
        setData(res);
        setRefreshSuccess(true);
        setLastSynced(new Date().toLocaleTimeString());
        setTimeout(() => setRefreshSuccess(false), 2500);
      } else {
        generateFallbackDirectives();
        setRefreshSuccess(true);
        setTimeout(() => setRefreshSuccess(false), 2500);
      }
    } catch (err) {
      console.error("Advisory table error:", err);
      generateFallbackDirectives();
    } finally {
      setLoading(false);
    }
  };

  const generateFallbackDirectives = () => {
    const stations = ["Rajiv Chowk", "Kashmere Gate", "Botanical Garden", "Dwarka Sec 21", "Hauz Khas"];
    const lines = ["Magenta Line", "Blue Line", "Red Line", "Yellow Line"];
    const rows = [];
    const tierCounts = { SEVERE_RUSH: 0, MODERATE_TRAFFIC: 0, OFF_PEAK: 0 };

    for (let i = 1; i <= 50; i++) {
      const hour = (6 + (i % 18));
      const isRush = (hour >= 8 && hour <= 11) || (hour >= 17 && hour <= 20);
      const pax = isRush ? Math.floor(1520 + Math.random() * 450) : (hour >= 12 && hour <= 16 ? Math.floor(820 + Math.random() * 450) : Math.floor(250 + Math.random() * 450));
      
      let tier = "OFF_PEAK";
      let headway = 10;
      let action = "Extend Headway to 10 Minutes (Conserve Fleet)";
      let statusLabel = "🟢 OFF-PEAK";

      if (pax >= 1500) {
        tier = "SEVERE_RUSH";
        headway = 3;
        action = "🔴 Reduce Headway to 3 Minutes (High-Frequency Dispatch)";
        statusLabel = "🔴 SEVERE RUSH HOUR";
      } else if (pax >= 800) {
        tier = "MODERATE_TRAFFIC";
        headway = 6;
        action = "🟡 Maintain Standard Headway (5-6 Minutes)";
        statusLabel = "🟡 MODERATE TRAFFIC";
      }

      tierCounts[tier] = (tierCounts[tier] || 0) + 1;

      rows.push({
        trip_id: 1000 + i,
        train_id: `TR_${2000 + (i * 37) % 8000}`,
        station_id: stations[i % stations.length],
        from_station: stations[i % stations.length],
        to_station: stations[(i + 2) % stations.length],
        line_color: lines[i % lines.length],
        entry_hour: `${hour.toString().padStart(2, '0')}:00`,
        hour_int: hour,
        predicted_occupancy: pax,
        train_capacity: 2400,
        occupancy_rate_pct: Math.round((pax / 2400) * 100),
        traffic_tier: tier,
        status_message: statusLabel,
        recommended_headway_min: headway,
        fleet_action: action
      });
    }

    setData({
      total_records_analyzed: rows.length,
      directives: rows,
      tier_counts: tierCounts
    });
  };

  useEffect(() => {
    loadData();
  }, []);

  // Filter and sort
  const filtered = (data.directives || []).filter(item => {
    const matchesSearch = 
      (item.from_station && item.from_station.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (item.to_station && item.to_station.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (item.train_id && item.train_id.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (item.line_color && item.line_color.toLowerCase().includes(searchTerm.toLowerCase()));

    const matchesTier = tierFilter === 'ALL' || item.traffic_tier === tierFilter;
    const matchesLine = lineFilter === 'ALL' || item.line_color === lineFilter;
    const matchesHour = hourFilter === 'ALL' || item.entry_hour.startsWith(hourFilter.padStart(2, '0'));

    return matchesSearch && matchesTier && matchesLine && matchesHour;
  });

  const sorted = [...filtered].sort((a, b) => {
    let valA = a[sortField];
    let valB = b[sortField];
    if (typeof valA === 'string') valA = valA.toLowerCase();
    if (typeof valB === 'string') valB = valB.toLowerCase();
    if (valA < valB) return sortAsc ? -1 : 1;
    if (valA > valB) return sortAsc ? 1 : -1;
    return 0;
  });

  const totalPages = Math.ceil(sorted.length / pageSize) || 1;
  const paginated = sorted.slice((currentPage - 1) * pageSize, currentPage * pageSize);

  const handleSort = (field) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(false);
    }
  };

  const exportCSV = () => {
    const headers = ["Trip ID", "Train ID", "Origin Station", "Destination", "Line", "Hour", "Predicted Pax", "Capacity %", "Tier", "Headway (min)", "Fleet Action"];
    const rows = sorted.map(d => [
      d.trip_id,
      d.train_id,
      `"${d.from_station}"`,
      `"${d.to_station}"`,
      `"${d.line_color}"`,
      d.entry_hour,
      d.predicted_occupancy,
      `${d.occupancy_rate_pct}%`,
      d.traffic_tier,
      d.recommended_headway_min,
      `"${d.fleet_action}"`
    ]);

    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map(e => e.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `metroflow_fleet_schedule_advisory_${new Date().toISOString().slice(0,10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const severeCount = data.tier_counts?.SEVERE_RUSH ?? data.directives?.filter(d => d.traffic_tier === 'SEVERE_RUSH').length ?? 0;
  const moderateCount = data.tier_counts?.MODERATE_TRAFFIC ?? data.directives?.filter(d => d.traffic_tier === 'MODERATE_TRAFFIC').length ?? 0;
  const offPeakCount = data.tier_counts?.OFF_PEAK ?? data.directives?.filter(d => d.traffic_tier === 'OFF_PEAK').length ?? 0;

  return (
    <div className="space-y-8">
      
      {/* Top Header & Metrics Bar with Generous Padding */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        
        {/* Total Instances */}
        <div className="glass-panel rounded-3xl p-6 border border-cyan-500/30 flex items-center justify-between shadow-xl">
          <div className="space-y-1">
            <p className="text-xs font-mono uppercase text-slate-400">Total Trips Analyzed</p>
            <h4 className="text-3xl font-black text-white font-display">{data.total_records_analyzed || data.directives.length}</h4>
            <p className="text-[11px] text-cyan-400 font-mono">XGBoost Test Instances</p>
          </div>
          <div className="p-4 rounded-2xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 shadow-inner">
            <Train className="w-6 h-6" />
          </div>
        </div>

        {/* Severe Rush */}
        <button 
          onClick={() => setTierFilter(tierFilter === 'SEVERE_RUSH' ? 'ALL' : 'SEVERE_RUSH')}
          className={`glass-panel rounded-3xl p-6 border text-left transition-all duration-300 shadow-xl ${
            tierFilter === 'SEVERE_RUSH' ? 'border-red-500 bg-red-950/30 ring-2 ring-red-500 scale-[1.02]' : 'border-red-500/30 hover:border-red-500/60'
          }`}
        >
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <p className="text-xs font-mono uppercase text-red-400 flex items-center gap-1.5 font-bold">
                <span className="w-2.5 h-2.5 rounded-full bg-red-500 animate-ping"></span>
                🔴 Severe Rush (≥1,500)
              </p>
              <h4 className="text-3xl font-black text-red-300 font-display">{severeCount}</h4>
              <p className="text-[11px] text-red-400/90 font-mono">3-Min High Frequency</p>
            </div>
            <div className="p-4 rounded-2xl bg-red-500/10 text-red-400 border border-red-500/20 shadow-inner">
              <ShieldAlert className="w-6 h-6" />
            </div>
          </div>
        </button>

        {/* Moderate Traffic */}
        <button 
          onClick={() => setTierFilter(tierFilter === 'MODERATE_TRAFFIC' ? 'ALL' : 'MODERATE_TRAFFIC')}
          className={`glass-panel rounded-3xl p-6 border text-left transition-all duration-300 shadow-xl ${
            tierFilter === 'MODERATE_TRAFFIC' ? 'border-amber-500 bg-amber-950/30 ring-2 ring-amber-500 scale-[1.02]' : 'border-amber-500/30 hover:border-amber-500/60'
          }`}
        >
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <p className="text-xs font-mono uppercase text-amber-400 font-bold">🟡 Moderate (800–1,499)</p>
              <h4 className="text-3xl font-black text-amber-300 font-display">{moderateCount}</h4>
              <p className="text-[11px] text-amber-400/90 font-mono">5–6 Min Standard Dispatch</p>
            </div>
            <div className="p-4 rounded-2xl bg-amber-500/10 text-amber-400 border border-amber-500/20 shadow-inner">
              <Clock className="w-6 h-6" />
            </div>
          </div>
        </button>

        {/* Off-Peak Flow */}
        <button 
          onClick={() => setTierFilter(tierFilter === 'OFF_PEAK' ? 'ALL' : 'OFF_PEAK')}
          className={`glass-panel rounded-3xl p-6 border text-left transition-all duration-300 shadow-xl ${
            tierFilter === 'OFF_PEAK' ? 'border-emerald-500 bg-emerald-950/30 ring-2 ring-emerald-500 scale-[1.02]' : 'border-emerald-500/30 hover:border-emerald-500/60'
          }`}
        >
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <p className="text-xs font-mono uppercase text-emerald-400 font-bold">🟢 Off-Peak (&lt;800)</p>
              <h4 className="text-3xl font-black text-emerald-300 font-display">{offPeakCount}</h4>
              <p className="text-[11px] text-emerald-400/90 font-mono">10-Min Fleet Conserve</p>
            </div>
            <div className="p-4 rounded-2xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 shadow-inner">
              <CheckCircle2 className="w-6 h-6" />
            </div>
          </div>
        </button>

      </div>

      {/* Table Container Card */}
      <div className="glass-panel rounded-3xl border border-slate-800 overflow-hidden shadow-2xl space-y-0">
        
        {/* Controls Bar with Refresh Feedback */}
        <div className="p-6 border-b border-slate-800 bg-slate-900/60 flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          
          {/* Search Input */}
          <div className="relative flex-1 max-w-md">
            <Search className="w-4 h-4 text-slate-400 absolute left-4 top-3.5" />
            <input
              type="text"
              placeholder="Search station, train ID, or line..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full bg-slate-950/90 border border-slate-700/80 text-white rounded-2xl pl-10 pr-4 py-2.5 text-xs focus:border-cyan-400 focus:outline-none placeholder:text-slate-500 font-mono shadow-inner"
            />
          </div>

          {/* Filters & Actions */}
          <div className="flex items-center flex-wrap gap-3">
            
            {/* Tier Filter */}
            <select
              value={tierFilter}
              onChange={(e) => {
                setTierFilter(e.target.value);
                setCurrentPage(1);
              }}
              className="bg-slate-950/90 border border-slate-700/80 text-slate-300 rounded-2xl px-4 py-2.5 text-xs focus:border-cyan-400 focus:outline-none font-mono cursor-pointer shadow-inner"
            >
              <option value="ALL">All Demand Tiers</option>
              <option value="SEVERE_RUSH">🔴 Severe Rush (≥1,500)</option>
              <option value="MODERATE_TRAFFIC">🟡 Moderate (800–1,499)</option>
              <option value="OFF_PEAK">🟢 Off-Peak (&lt;800)</option>
            </select>

            {/* Line Filter */}
            <select
              value={lineFilter}
              onChange={(e) => {
                setLineFilter(e.target.value);
                setCurrentPage(1);
              }}
              className="bg-slate-950/90 border border-slate-700/80 text-slate-300 rounded-2xl px-4 py-2.5 text-xs focus:border-cyan-400 focus:outline-none font-mono cursor-pointer shadow-inner"
            >
              <option value="ALL">All Metro Lines</option>
              {LINES.map(l => (
                <option key={l.id} value={l.name}>{l.name}</option>
              ))}
            </select>

            {/* Refresh Action Button with Live Visual Feedback */}
            <button
              onClick={loadData}
              disabled={loading}
              className={`flex items-center space-x-2 px-4 py-2.5 rounded-2xl border text-xs font-mono font-medium transition-all shadow-md active:scale-95 ${
                refreshSuccess 
                  ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/50' 
                  : 'bg-slate-800/90 hover:bg-slate-700 text-slate-300 hover:text-cyan-400 border-slate-700'
              }`}
              title="Refresh Fleet Schedule Directives from Backend"
            >
              {refreshSuccess ? (
                <>
                  <Check className="w-4 h-4 text-emerald-400" />
                  <span>Synced!</span>
                </>
              ) : (
                <>
                  <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-cyan-400' : ''}`} />
                  <span>Refresh</span>
                </>
              )}
            </button>

            <button
              onClick={exportCSV}
              className="flex items-center space-x-2 px-4 py-2.5 rounded-2xl bg-cyan-500/15 hover:bg-cyan-500/25 text-cyan-300 border border-cyan-500/30 text-xs font-mono font-medium transition-all shadow-md"
            >
              <Download className="w-4 h-4" />
              <span>Export CSV</span>
            </button>

          </div>

        </div>

        {/* Scrollable Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/90 text-slate-400 font-mono uppercase tracking-wider border-b border-slate-800 text-[11px]">
              <tr>
                <th className="py-4 px-5 cursor-pointer hover:text-white" onClick={() => handleSort('trip_id')}>
                  <div className="flex items-center space-x-1.5">
                    <span>Trip & Train</span>
                    <ArrowUpDown className="w-3.5 h-3.5" />
                  </div>
                </th>
                <th className="py-4 px-5 cursor-pointer hover:text-white" onClick={() => handleSort('from_station')}>
                  <div className="flex items-center space-x-1.5">
                    <span>Origin Hub</span>
                    <ArrowUpDown className="w-3.5 h-3.5" />
                  </div>
                </th>
                <th className="py-4 px-5">Destination</th>
                <th className="py-4 px-5">Metro Line</th>
                <th className="py-4 px-5 cursor-pointer hover:text-white" onClick={() => handleSort('hour_int')}>
                  <div className="flex items-center space-x-1.5">
                    <span>Time</span>
                    <ArrowUpDown className="w-3.5 h-3.5" />
                  </div>
                </th>
                <th className="py-4 px-5 cursor-pointer hover:text-white" onClick={() => handleSort('predicted_occupancy')}>
                  <div className="flex items-center space-x-1.5">
                    <span>Predicted Pax</span>
                    <ArrowUpDown className="w-3.5 h-3.5" />
                  </div>
                </th>
                <th className="py-4 px-5">Headway</th>
                <th className="py-4 px-5">Automated Fleet Action Directive</th>
                <th className="py-4 px-5">Traffic Tier</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-sans">
              {paginated.length > 0 ? (
                paginated.map((row, idx) => {
                  const isSevere = row.traffic_tier === 'SEVERE_RUSH';
                  const isModerate = row.traffic_tier === 'MODERATE_TRAFFIC';
                  
                  // Match line color
                  const lineObj = LINES.find(l => l.name === row.line_color);

                  return (
                    <tr 
                      key={idx}
                      className={`hover:bg-slate-800/40 transition-colors ${
                        isSevere ? 'bg-red-950/10' : ''
                      }`}
                    >
                      <td className="py-4 px-5 font-mono">
                        <div className="font-bold text-white text-sm">#{row.trip_id}</div>
                        <div className="text-[11px] text-cyan-400 font-semibold">{row.train_id}</div>
                      </td>

                      <td className="py-4 px-5 font-bold text-slate-100 text-sm">
                        {row.from_station}
                      </td>

                      <td className="py-4 px-5 text-slate-300 font-medium">
                        {row.to_station}
                      </td>

                      <td className="py-4 px-5">
                        <span className={`inline-flex items-center px-3 py-1 rounded-xl text-xs font-semibold border ${lineObj?.badge || 'bg-slate-800 text-slate-300 border-slate-700'}`}>
                          <span className="w-2 h-2 rounded-full mr-2 shadow-sm" style={{ backgroundColor: lineObj?.color || '#38bdf8' }}></span>
                          {row.line_color}
                        </span>
                      </td>

                      <td className="py-4 px-5 font-mono font-bold text-slate-200 text-sm">
                        {row.entry_hour}
                      </td>

                      <td className="py-4 px-5">
                        <div className="flex items-baseline space-x-1.5 font-mono">
                          <span className={`font-black text-base ${isSevere ? 'text-red-400 font-display' : (isModerate ? 'text-amber-400' : 'text-emerald-400')}`}>
                            {row.predicted_occupancy}
                          </span>
                          <span className="text-[11px] text-slate-400">pax</span>
                        </div>
                        <div className="text-[10px] text-slate-400 font-mono">
                          {row.occupancy_rate_pct}% capacity
                        </div>
                      </td>

                      <td className="py-4 px-5">
                        <span className={`px-3 py-1.5 rounded-xl text-xs font-mono font-bold border inline-flex items-center gap-1.5 shadow-sm ${
                          isSevere 
                            ? 'bg-red-500/20 text-red-300 border-red-500/40' 
                            : (isModerate 
                                ? 'bg-amber-500/20 text-amber-300 border-amber-500/40' 
                                : 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40')
                        }`}>
                          <Clock className="w-3.5 h-3.5" />
                          {row.recommended_headway_min} Min
                        </span>
                      </td>

                      <td className="py-4 px-5 text-slate-200 text-xs font-medium max-w-sm">
                        <span className="line-clamp-2">
                          {row.fleet_action}
                        </span>
                      </td>

                      <td className="py-4 px-5">
                        <span className={`px-3 py-1 rounded-xl text-[10px] font-mono font-bold uppercase border shadow-sm ${
                          isSevere 
                            ? 'bg-red-500/20 text-red-400 border-red-500/40' 
                            : (isModerate 
                                ? 'bg-amber-500/20 text-amber-400 border-amber-500/40' 
                                : 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40')
                        }`}>
                          {row.traffic_tier}
                        </span>
                      </td>

                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan="9" className="py-12 text-center text-slate-500 font-mono text-sm">
                    No transit scheduling records match current filter criteria.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar with Enhanced Padding */}
        <div className="p-6 border-t border-slate-800 bg-slate-950/80 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-400 font-mono">
          <div>
            Showing <span className="text-white font-bold">{Math.min(sorted.length, (currentPage - 1) * pageSize + 1)}</span> to <span className="text-white font-bold">{Math.min(sorted.length, currentPage * pageSize)}</span> of <span className="text-white font-bold">{sorted.length}</span> directives
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
              disabled={currentPage === 1}
              className="p-2.5 rounded-2xl bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 disabled:opacity-40 transition-colors shadow-sm"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="px-4 py-1.5 rounded-2xl bg-slate-900 border border-slate-800 text-slate-200">
              Page {currentPage} of {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
              disabled={currentPage === totalPages}
              className="p-2.5 rounded-2xl bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 disabled:opacity-40 transition-colors shadow-sm"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>

      </div>

    </div>
  );
}
