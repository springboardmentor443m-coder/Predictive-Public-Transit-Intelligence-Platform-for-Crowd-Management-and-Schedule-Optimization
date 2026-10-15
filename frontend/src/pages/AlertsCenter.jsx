import React, { useState, useMemo } from 'react';
import {
  AlertTriangle,
  CheckCircle,
  Download,
  Filter,
  PlusCircle,
  Clock,
  ShieldAlert,
  Search,
  Check,
  Send,
} from 'lucide-react';
import StatusBadge from '../components/StatusBadge';
import MetricCard from '../components/MetricCard';

export default function AlertsCenter({ alerts = [], onAcknowledgeAlert, onResolveAlert, onAddAlert }) {
  const [severityFilter, setSeverityFilter] = useState('All');
  const [boroughFilter, setBoroughFilter] = useState('All');
  const [statusFilter, setStatusFilter] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');

  // Form for custom manual alert
  const [showAddForm, setShowAddForm] = useState(false);
  const [customStation, setCustomStation] = useState('');
  const [customBorough, setCustomBorough] = useState('Manhattan');
  const [customSeverity, setCustomSeverity] = useState('High');
  const [customMessage, setCustomMessage] = useState('');
  const [customRec, setCustomRec] = useState('Deploy standby units immediately.');

  const filteredAlerts = useMemo(() => {
    return alerts.filter((a) => {
      const matchSearch =
        !searchQuery ||
        a.station.toLowerCase().includes(searchQuery.toLowerCase()) ||
        a.message.toLowerCase().includes(searchQuery.toLowerCase());

      const matchSev =
        severityFilter === 'All' ||
        a.severity?.toLowerCase() === severityFilter.toLowerCase() ||
        a.level?.toLowerCase() === severityFilter.toLowerCase();

      const matchBorough =
        boroughFilter === 'All' ||
        a.borough?.toLowerCase() === boroughFilter.toLowerCase();

      const matchStatus =
        statusFilter === 'All' ||
        a.status?.toLowerCase() === statusFilter.toLowerCase();

      return matchSearch && matchSev && matchBorough && matchStatus;
    });
  }, [alerts, searchQuery, severityFilter, boroughFilter, statusFilter]);

  const highCount = alerts.filter((a) => (a.severity || a.level) === 'High').length;
  const medCount = alerts.filter((a) => (a.severity || a.level) === 'Medium').length;
  const resolvedCount = alerts.filter((a) => a.status === 'Resolved').length;

  const handleExportCSV = () => {
    const headers = ['Alert ID', 'Timestamp', 'Station', 'Borough', 'Severity', 'Message', 'Recommendation', 'Status'];
    const rows = filteredAlerts.map((a) => [
      `"${a.id}"`,
      `"${a.timestamp}"`,
      `"${a.station}"`,
      `"${a.borough}"`,
      `"${a.severity || a.level}"`,
      `"${a.message.replace(/"/g, '""')}"`,
      `"${(a.recommendation || '').replace(/"/g, '""')}"`,
      `"${a.status || 'Active'}"`,
    ]);

    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `metroflow_alerts_log_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleCreateAlert = (e) => {
    e.preventDefault();
    if (!customStation || !customMessage) return;
    const newAlert = {
      id: `ALT-${Date.now().toString().slice(-4)}`,
      timestamp: new Date().toLocaleTimeString(),
      station: customStation,
      borough: customBorough,
      severity: customSeverity,
      level: customSeverity,
      message: customMessage,
      recommendation: customRec,
      status: 'Active',
    };
    if (onAddAlert) onAddAlert(newAlert);
    setCustomStation('');
    setCustomMessage('');
    setShowAddForm(false);
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="ops-panel p-5 bg-gradient-to-r from-[#111827] via-slate-900 to-[#1F293D] flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-rose-500/10 text-rose-400 border border-rose-500/20">
              SAFETY & EMERGENCY DIRECTIVES
            </span>
            <span className="text-xs text-slate-400 font-mono">
              INCIDENT RESPONSE CENTER
            </span>
          </div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <AlertTriangle size={20} className="text-[#EF4444]" />
            <span>Alerts & Rapid Incident Dispatch Center</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Real-time surveillance of platform overcrowding, passenger surges, and automated transit notifications.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className="btn-primary text-xs"
          >
            <PlusCircle size={14} />
            <span>{showAddForm ? 'Cancel Manual Alert' : 'Create Incident Notice'}</span>
          </button>

          <button onClick={handleExportCSV} className="btn-secondary text-xs">
            <Download size={14} />
            <span>Export Alerts CSV</span>
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <MetricCard
          title="Active Critical Alerts"
          value={highCount}
          delta={highCount > 0 ? 'Surge Protocol Active' : 'Normal'}
          deltaType={highCount > 0 ? 'negative' : 'positive'}
          subtext="Immediate dispatch required"
          icon={AlertTriangle}
          accentColor="#EF4444"
        />

        <MetricCard
          title="Active Warnings"
          value={medCount}
          delta="Platform Inflow Watch"
          deltaType="warning"
          subtext="Moderate passenger density"
          icon={Clock}
          accentColor="#F59E0B"
        />

        <MetricCard
          title="Resolved Incident Log"
          value={resolvedCount}
          delta="Awaiting Cleared Tiers"
          deltaType="positive"
          subtext="Handled in active session"
          icon={CheckCircle}
          accentColor="#10B981"
        />
      </div>

      {/* Manual Alert Form Drawer */}
      {showAddForm && (
        <div className="ops-panel p-5 border border-teal-500/30 bg-slate-900/90 space-y-4 animate-in fade-in duration-150">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <Send size={15} className="text-[#00D4AA]" />
            <span>Dispatch Custom Simulated Transit Notice</span>
          </h3>

          <form onSubmit={handleCreateAlert} className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-[11px] font-semibold text-slate-300 uppercase mb-1">
                Subway Station
              </label>
              <input
                type="text"
                placeholder="e.g. 14 St - Union Sq"
                value={customStation}
                onChange={(e) => setCustomStation(e.target.value)}
                className="ops-input text-xs"
                required
              />
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-slate-300 uppercase mb-1">
                Borough
              </label>
              <select
                value={customBorough}
                onChange={(e) => setCustomBorough(e.target.value)}
                className="ops-select text-xs"
              >
                <option value="Manhattan">Manhattan</option>
                <option value="Brooklyn">Brooklyn</option>
                <option value="Queens">Queens</option>
                <option value="Bronx">Bronx</option>
              </select>
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-slate-300 uppercase mb-1">
                Severity Level
              </label>
              <select
                value={customSeverity}
                onChange={(e) => setCustomSeverity(e.target.value)}
                className="ops-select text-xs"
              >
                <option value="High">🚨 High / Critical</option>
                <option value="Medium">⚠️ Medium / Warning</option>
                <option value="Low">✅ Low / Informational</option>
              </select>
            </div>

            <div className="md:col-span-2">
              <label className="block text-[11px] font-semibold text-slate-300 uppercase mb-1">
                Incident Message
              </label>
              <input
                type="text"
                placeholder="e.g. Overcrowding surge detected on uptown platform."
                value={customMessage}
                onChange={(e) => setCustomMessage(e.target.value)}
                className="ops-input text-xs"
                required
              />
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-slate-300 uppercase mb-1">
                Operational Recommendation
              </label>
              <input
                type="text"
                value={customRec}
                onChange={(e) => setCustomRec(e.target.value)}
                className="ops-input text-xs"
              />
            </div>

            <div className="md:col-span-3 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setShowAddForm(false)}
                className="btn-secondary text-xs"
              >
                Cancel
              </button>
              <button type="submit" className="btn-primary text-xs">
                Broadcast Alert
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Filter Bar */}
      <div className="ops-panel p-4 space-y-3">
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
          <div className="relative">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search station or message..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="ops-input pl-8 text-xs py-1.5"
            />
          </div>

          <div>
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="ops-select text-xs py-1.5"
            >
              <option value="All">All Severities</option>
              <option value="High">🚨 High Severity Only</option>
              <option value="Medium">⚠️ Medium Severity Only</option>
              <option value="Low">✅ Low Severity Only</option>
            </select>
          </div>

          <div>
            <select
              value={boroughFilter}
              onChange={(e) => setBoroughFilter(e.target.value)}
              className="ops-select text-xs py-1.5"
            >
              <option value="All">All Boroughs</option>
              <option value="Manhattan">Manhattan</option>
              <option value="Brooklyn">Brooklyn</option>
              <option value="Queens">Queens</option>
              <option value="Bronx">Bronx</option>
            </select>
          </div>

          <div>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="ops-select text-xs py-1.5"
            >
              <option value="All">All Statuses</option>
              <option value="Active">Active Alerts</option>
              <option value="Acknowledged">Acknowledged</option>
              <option value="Resolved">Resolved</option>
            </select>
          </div>
        </div>
      </div>

      {/* Main Alerts Table */}
      <div className="ops-panel p-5">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <ShieldAlert size={16} className="text-[#38BDF8]" />
            <span>Incident Telemetry Logbook ({filteredAlerts.length})</span>
          </h3>
          <span className="text-xs font-mono text-slate-500">
            Session Memory Buffer
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="ops-table">
            <thead>
              <tr>
                <th>Alert ID</th>
                <th>Time</th>
                <th>Station</th>
                <th>Borough</th>
                <th>Severity</th>
                <th>Operational Message</th>
                <th>Directive</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {filteredAlerts.length > 0 ? (
                filteredAlerts.map((alert) => (
                  <tr key={alert.id} className="hover:bg-slate-800/40">
                    <td className="font-mono text-xs font-semibold text-slate-400">
                      {alert.id}
                    </td>
                    <td className="font-mono text-xs text-slate-300">
                      {alert.timestamp}
                    </td>
                    <td className="font-semibold text-white">
                      {alert.station}
                    </td>
                    <td className="text-slate-400">{alert.borough}</td>
                    <td>
                      <StatusBadge status={alert.severity || alert.level} size="sm" />
                    </td>
                    <td className="text-slate-200 text-xs max-w-xs leading-relaxed">
                      {alert.message}
                    </td>
                    <td className="text-[#00D4AA] text-xs font-medium max-w-xs truncate">
                      {alert.recommendation}
                    </td>
                    <td>
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                          alert.status === 'Resolved'
                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                            : alert.status === 'Acknowledged'
                            ? 'bg-sky-500/10 text-sky-400 border border-sky-500/30'
                            : 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                        }`}
                      >
                        {alert.status || 'Active'}
                      </span>
                    </td>
                    <td>
                      <div className="flex items-center gap-1.5">
                        {alert.status !== 'Acknowledged' && alert.status !== 'Resolved' && (
                          <button
                            onClick={() => onAcknowledgeAlert && onAcknowledgeAlert(alert.id)}
                            className="px-2 py-0.5 rounded text-[11px] bg-slate-800 hover:bg-slate-700 text-sky-400 transition"
                            title="Acknowledge alert"
                          >
                            Ack
                          </button>
                        )}
                        {alert.status !== 'Resolved' && (
                          <button
                            onClick={() => onResolveAlert && onResolveAlert(alert.id)}
                            className="px-2 py-0.5 rounded text-[11px] bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 transition"
                            title="Mark as resolved"
                          >
                            Resolve
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={9} className="text-center py-10 text-slate-500 text-xs">
                    No incident alerts match selected filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <div className="mt-4 pt-3 border-t border-slate-800 text-[10px] text-slate-500">
          <strong>Memory Notice:</strong> Incident events are maintained in the active web browser session memory for presentation and dispatch drill workflows. No external historical incidents database is connected.
        </div>
      </div>
    </div>
  );
}
