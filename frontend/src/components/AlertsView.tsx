import React, { useEffect, useState } from 'react';
import { Bell, AlertTriangle, AlertCircle, ShieldAlert, Radio, CheckCircle, Send, Plus } from 'lucide-react';
import { api } from '../services/api';
import { Alert, User } from '../types';

interface AlertsViewProps {
  currentUser: User | null;
}

export const AlertsView: React.FC<AlertsViewProps> = ({ currentUser }) => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [activeCount, setActiveCount] = useState(0);
  const [filterCategory, setFilterCategory] = useState('ALL');
  const [loading, setLoading] = useState(true);

  // Broadcast modal form
  const [showBroadcastModal, setShowBroadcastModal] = useState(false);
  const [severity, setSeverity] = useState('warning');
  const [category, setCategory] = useState('overcrowding');
  const [stationName, setStationName] = useState('Times Sq - 42 St');
  const [line, setLine] = useState('1');
  const [message, setMessage] = useState('');
  const [broadcastSuccess, setBroadcastSuccess] = useState<string | null>(null);

  const fetchAlerts = async () => {
    try {
      const data = await api.getAlerts();
      setAlerts(data.alerts);
      setActiveCount(data.active_count);
    } catch (err) {
      console.error('Failed to load alerts', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
    const interval = setInterval(fetchAlerts, 4000);
    return () => clearInterval(interval);
  }, []);

  const handleResolve = async (alertId: number) => {
    try {
      await api.resolveAlert(alertId);
      fetchAlerts();
    } catch (err) {
      console.error('Failed to resolve alert', err);
    }
  };

  const handleBroadcast = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message) return;
    try {
      await api.broadcastAlert({
        severity,
        category,
        station_name: stationName,
        line,
        message
      });
      setBroadcastSuccess('Operational announcement broadcasted across network displays.');
      setMessage('');
      setShowBroadcastModal(false);
      fetchAlerts();
      setTimeout(() => setBroadcastSuccess(null), 4000);
    } catch (err: any) {
      alert(`Broadcast failed: ${err.message}`);
    }
  };

  const filteredAlerts = alerts.filter(a => {
    if (filterCategory === 'ALL') return true;
    return a.category.toLowerCase() === filterCategory.toLowerCase();
  });

  const getSeverityBadge = (sev: string) => {
    switch (sev.toLowerCase()) {
      case 'emergency':
        return <span className="px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase bg-red-600 text-white animate-pulse">EMERGENCY</span>;
      case 'critical':
        return <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase bg-red-500/20 text-red-400 border border-red-500/30">CRITICAL</span>;
      case 'warning':
        return <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase bg-amber-500/20 text-amber-400 border border-amber-500/30">WARNING</span>;
      default:
        return <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase bg-blue-500/20 text-blue-400 border border-blue-500/30">INFO</span>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header and Broadcast Action */}
      <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl flex flex-col md:flex-row items-start md:items-center justify-between gap-4 shadow-xl">
        <div className="flex items-center space-x-3.5">
          <div className="p-3 bg-red-600/20 text-red-400 rounded-2xl border border-red-500/30">
            <Bell className="w-7 h-7" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-xl font-black text-white">Alerts & Emergency Notification System</h2>
              <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-red-500/20 text-red-300 border border-red-500/30">
                {activeCount} Active Warnings
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Live automated crowd congestion alerts, train delay advisories, and emergency broadcast dispatch.
            </p>
          </div>
        </div>

        <button
          onClick={() => setShowBroadcastModal(true)}
          className="px-5 py-2.5 bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-500 hover:to-rose-500 text-white rounded-xl text-xs font-bold transition shadow-lg shadow-red-600/20 flex items-center space-x-2 cursor-pointer"
        >
          <Radio className="w-4 h-4" />
          <span>Broadcast Emergency Announcement</span>
        </button>
      </div>

      {broadcastSuccess && (
        <div className="p-3.5 bg-emerald-500/20 border border-emerald-500/40 rounded-xl text-xs text-emerald-300 flex items-center space-x-2">
          <CheckCircle className="w-4 h-4 flex-shrink-0" />
          <span>{broadcastSuccess}</span>
        </div>
      )}

      {/* Filter Tabs */}
      <div className="flex items-center justify-between">
        <div className="flex space-x-2">
          {['ALL', 'Overcrowding', 'Delay', 'Emergency'].map(cat => (
            <button
              key={cat}
              onClick={() => setFilterCategory(cat)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition cursor-pointer ${
                filterCategory === cat
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-600/20'
                  : 'bg-slate-900 text-slate-400 hover:text-white border border-slate-800'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
        <span className="text-xs text-slate-400 font-mono">Showing {filteredAlerts.length} Alerts</span>
      </div>

      {/* Alerts Grid / List */}
      <div className="space-y-3">
        {filteredAlerts.map(alert => {
          const isActive = Boolean(alert.is_active);
          return (
            <div
              key={alert.id}
              className={`p-4 rounded-2xl border transition shadow-md flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 ${
                isActive
                  ? alert.severity === 'emergency'
                    ? 'bg-red-950/40 border-red-500/70'
                    : 'bg-slate-900 border-slate-800 hover:border-slate-700'
                  : 'bg-slate-950/60 border-slate-900 opacity-60'
              }`}
            >
              <div className="space-y-1.5 max-w-2xl">
                <div className="flex items-center space-x-2.5">
                  {getSeverityBadge(alert.severity)}
                  <span className="text-xs font-bold text-white capitalize">{alert.category} Alert</span>
                  {alert.line && (
                    <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-slate-800 text-slate-300">
                      Line {alert.line}
                    </span>
                  )}
                  {alert.station_name && (
                    <span className="text-xs text-slate-400">&bull; {alert.station_name}</span>
                  )}
                  <span className="text-[10px] text-slate-500 font-mono">{alert.timestamp}</span>
                </div>
                <p className="text-xs text-slate-200">{alert.message}</p>
                {!isActive && alert.resolved_by && (
                  <div className="text-[10px] text-emerald-400">
                    &check; Resolved by {alert.resolved_by}
                  </div>
                )}
              </div>

              <div className="flex items-center space-x-2 flex-shrink-0">
                {isActive ? (
                  <button
                    onClick={() => handleResolve(alert.id)}
                    className="px-3 py-1.5 bg-slate-800 hover:bg-emerald-600 text-slate-300 hover:text-white rounded-xl text-xs font-semibold transition cursor-pointer flex items-center space-x-1.5"
                  >
                    <CheckCircle className="w-3.5 h-3.5" />
                    <span>Acknowledge & Clear</span>
                  </button>
                ) : (
                  <span className="text-xs text-slate-500 font-semibold px-2 py-1 bg-slate-900 rounded-lg">
                    Resolved
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Broadcast Modal */}
      {showBroadcastModal && (
        <div className="fixed inset-0 z-[2300] flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-lg shadow-2xl p-6 text-slate-100 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-white flex items-center space-x-2">
                <Radio className="w-5 h-5 text-red-400" />
                <span>Dispatch High-Priority Passenger Broadcast</span>
              </h3>
              <button
                onClick={() => setShowBroadcastModal(false)}
                className="text-slate-400 hover:text-white"
              >
                &times;
              </button>
            </div>

            <form onSubmit={handleBroadcast} className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Severity</label>
                  <select
                    value={severity}
                    onChange={e => setSeverity(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-blue-500"
                  >
                    <option value="emergency">Emergency (Highest Priority)</option>
                    <option value="critical">Critical</option>
                    <option value="warning">Warning / Congestion</option>
                    <option value="info">Informational</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Category</label>
                  <select
                    value={category}
                    onChange={e => setCategory(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-blue-500"
                  >
                    <option value="overcrowding">Overcrowding Surge</option>
                    <option value="delay">Line Schedule Delay</option>
                    <option value="emergency">Emergency / Evacuation</option>
                    <option value="maintenance">Platform Maintenance</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Station Hub</label>
                  <input
                    type="text"
                    value={stationName}
                    onChange={e => setStationName(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Corridor Line</label>
                  <input
                    type="text"
                    value={line}
                    onChange={e => setLine(e.target.value)}
                    placeholder="e.g. 1, 4, 7, ALL"
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Announcement Message</label>
                <textarea
                  rows={3}
                  value={message}
                  onChange={e => setMessage(e.target.value)}
                  placeholder="Enter passenger announcement text for display boards and audio PA..."
                  required
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-blue-500 placeholder-slate-500"
                ></textarea>
              </div>

              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowBroadcastModal(false)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-semibold cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 bg-red-600 hover:bg-red-500 text-white rounded-xl text-xs font-bold transition shadow-lg shadow-red-600/30 cursor-pointer flex items-center space-x-1.5"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>Transmit Broadcast</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
