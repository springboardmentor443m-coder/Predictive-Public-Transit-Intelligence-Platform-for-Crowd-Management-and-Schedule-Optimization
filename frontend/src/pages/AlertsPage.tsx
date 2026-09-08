import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import { Alert } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { MetricCard } from '../components/MetricCard';
import { useAuth } from '../context/AuthContext';
import {
  AlertTriangle,
  CheckCircle,
  Clock,
  Filter,
  ShieldCheck,
  RefreshCw,
  Bell,
  Lock,
} from 'lucide-react';

export const AlertsPage: React.FC = () => {
  const { user, isAuthenticated } = useAuth();
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [severityFilter, setSeverityFilter] = useState('');
  const [resolvedFilter, setResolvedFilter] = useState<string>('unresolved');
  const [loading, setLoading] = useState(true);
  const [resolvingId, setResolvingId] = useState<number | null>(null);

  const isOperatorOrAdmin =
    isAuthenticated && user && (user.role === 'admin' || user.role === 'operator');

  const loadAlerts = async () => {
    try {
      setLoading(true);
      const params: { severity?: string; resolved?: boolean } = {};
      if (severityFilter) params.severity = severityFilter;
      if (resolvedFilter === 'unresolved') params.resolved = false;
      if (resolvedFilter === 'resolved') params.resolved = true;

      const data = await api.getAlerts(params);
      setAlerts(data);
    } catch (err) {
      console.error('Failed to load alerts:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAlerts();
  }, [severityFilter, resolvedFilter]);

  const handleResolve = async (id: number) => {
    if (!isOperatorOrAdmin) {
      alert('Authentication required: Only operators or administrators can resolve incidents.');
      return;
    }

    try {
      setResolvingId(id);
      await api.resolveAlert(id);
      // Update local state
      setAlerts((prev) =>
        prev.map((a) => (a.id === id ? { ...a, resolved: true } : a))
      );
    } catch (err) {
      alert(`Failed to resolve alert: ${err}`);
    } finally {
      setResolvingId(null);
    }
  };

  const activeCount = alerts.filter((a) => !a.resolved).length;
  const criticalCount = alerts.filter((a) => !a.resolved && a.severity === 'critical').length;
  const highCount = alerts.filter((a) => !a.resolved && a.severity === 'high').length;

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-100 tracking-tight font-sans">
            Operational Alerts & Incident Response
          </h1>
          <p className="text-xs text-slate-400 font-mono mt-1">
            Real-time platform overcrowding thresholds and automated dispatch notifications
          </p>
        </div>

        <button
          onClick={loadAlerts}
          className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-bg-card hover:bg-slate-800 text-slate-300 border border-border-dark font-mono text-xs font-semibold transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5 text-metro-cyan" />
          <span>Refresh Feed</span>
        </button>
      </div>

      {/* Alert KPI Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <MetricCard
          title="Active Alerts"
          value={activeCount}
          subtitle="Unresolved incidents"
          icon={AlertTriangle}
          accentColor="amber"
        />
        <MetricCard
          title="Critical Overcrowding"
          value={criticalCount}
          subtitle="Platform density > 86%"
          icon={Bell}
          accentColor="crimson"
        />
        <MetricCard
          title="Elevated Density"
          value={highCount}
          subtitle="Platform density 68% - 85%"
          icon={Clock}
          accentColor="cyan"
        />
      </div>

      {/* Filters & Control Bar */}
      <div className="bg-bg-surface border border-border-dark rounded-2xl p-4 flex flex-wrap items-center justify-between gap-4 shadow-card">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-1.5 text-xs font-mono text-slate-400">
            <Filter className="w-4 h-4 text-metro-cyan" />
            <span>Severity:</span>
          </div>
          {['', 'critical', 'high', 'medium', 'low'].map((sev) => (
            <button
              key={sev}
              onClick={() => setSeverityFilter(sev)}
              className={`px-3 py-1 rounded-lg text-xs font-mono capitalize transition-all ${
                severityFilter === sev
                  ? 'bg-metro-cyan text-bg-main font-bold shadow-glow'
                  : 'bg-bg-card text-slate-400 border border-border-dark hover:text-slate-200'
              }`}
            >
              {sev || 'All'}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2 text-xs font-mono">
          <span className="text-slate-400">Status:</span>
          <select
            value={resolvedFilter}
            onChange={(e) => setResolvedFilter(e.target.value)}
            className="px-3 py-1.5 bg-bg-card border border-border-dark rounded-lg text-slate-200 text-xs font-mono focus:outline-none focus:border-metro-cyan"
          >
            <option value="">All Alerts</option>
            <option value="unresolved">Unresolved Only</option>
            <option value="resolved">Resolved History</option>
          </select>
        </div>
      </div>

      {/* Alerts Feed List */}
      <div className="space-y-3">
        {loading ? (
          <div className="p-8 text-center text-slate-400 font-mono text-xs">
            Loading incident feed...
          </div>
        ) : alerts.length === 0 ? (
          <div className="bg-bg-surface border border-border-dark rounded-2xl p-12 text-center text-slate-400 font-mono space-y-2">
            <CheckCircle className="w-8 h-8 text-emerald-400 mx-auto" />
            <p className="text-sm font-semibold text-slate-200">No matching alerts found</p>
            <p className="text-xs text-slate-500">
              Network platforms are operating within nominal thresholds.
            </p>
          </div>
        ) : (
          alerts.map((alert) => {
            const dt = new Date(alert.created_at);
            const timeFormatted = dt.toLocaleString('en-US', {
              timeZone: 'Asia/Seoul',
              month: 'short',
              day: 'numeric',
              hour: '2-digit',
              minute: '2-digit',
            });

            return (
              <div
                key={alert.id}
                className={`bg-bg-surface border rounded-2xl p-5 shadow-card transition-all flex flex-col md:flex-row md:items-center md:justify-between gap-4 ${
                  alert.resolved
                    ? 'border-border-dark opacity-60'
                    : alert.severity === 'critical'
                    ? 'border-red-800/80 bg-red-950/10 hover:shadow-critGlow'
                    : alert.severity === 'high'
                    ? 'border-amber-800/80 bg-amber-950/10'
                    : 'border-border-dark'
                }`}
              >
                {/* Left Details */}
                <div className="space-y-1.5 max-w-3xl">
                  <div className="flex flex-wrap items-center gap-2.5">
                    <StatusBadge status={alert.severity} size="sm" />
                    <span className="text-xs font-mono font-semibold text-slate-300">
                      Station {alert.station_code || 'Network-wide'}
                    </span>
                    <span className="text-slate-600">&bull;</span>
                    <span className="text-[11px] font-mono text-slate-400">
                      Type: <span className="uppercase text-slate-300">{alert.alert_type}</span>
                    </span>
                    <span className="text-slate-600">&bull;</span>
                    <span className="text-[11px] font-mono text-slate-400 flex items-center gap-1">
                      <Clock className="w-3 h-3 text-slate-500" />
                      {timeFormatted} KST
                    </span>
                  </div>

                  <p className="text-sm font-medium text-slate-200 leading-relaxed">
                    {alert.message}
                  </p>
                </div>

                {/* Right Action Button */}
                <div className="shrink-0 flex items-center gap-3">
                  {alert.resolved ? (
                    <span className="inline-flex items-center gap-1.5 text-xs font-mono text-emerald-400 font-semibold px-3 py-1.5 rounded-lg bg-emerald-950/30 border border-emerald-800/40">
                      <CheckCircle className="w-3.5 h-3.5" />
                      Resolved
                    </span>
                  ) : isOperatorOrAdmin ? (
                    <button
                      onClick={() => handleResolve(alert.id)}
                      disabled={resolvingId === alert.id}
                      className="px-4 py-2 rounded-lg bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/40 font-mono text-xs font-bold transition-all hover:shadow-[0_0_15px_rgba(16,185,129,0.3)] disabled:opacity-50"
                    >
                      {resolvingId === alert.id ? 'Resolving...' : 'Mark Resolved'}
                    </button>
                  ) : (
                    <div
                      title="Operator or Administrator role required to resolve incidents"
                      className="flex items-center gap-1.5 text-xs font-mono text-slate-500 px-3 py-1.5 rounded-lg bg-bg-card border border-border-dark cursor-not-allowed"
                    >
                      <Lock className="w-3.5 h-3.5" />
                      <span>Operator Action</span>
                    </div>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
