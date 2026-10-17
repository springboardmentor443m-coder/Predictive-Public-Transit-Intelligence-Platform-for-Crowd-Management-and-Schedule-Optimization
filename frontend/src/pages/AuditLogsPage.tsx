import React, { useState, useEffect } from 'react';
import { AuditLog } from '../types/audit';
import { auditService } from '../services/auditService';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { ShieldAlert, RefreshCw, Filter, Clock } from 'lucide-react';

export const AuditLogsPage: React.FC = () => {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [actionFilter, setActionFilter] = useState<string>('');
  const [emailFilter, setEmailFilter] = useState<string>('');

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const data = await auditService.getAuditLogs(actionFilter || undefined, emailFilter || undefined);
      setLogs(data);
    } catch (e) {
      console.error('Failed to fetch audit logs:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [actionFilter]);

  const handleFilterSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchLogs();
  };

  const getActionBadgeVariant = (action: string) => {
    if (action.includes('SUCCESS') || action.includes('CREATED')) return 'emerald';
    if (action.includes('FAILED') || action.includes('BLOCKED')) return 'rose';
    if (action.includes('ROLE') || action.includes('STATUS')) return 'purple';
    if (action.includes('UPDATE')) return 'amber';
    return 'cyan';
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-extrabold text-slate-100 font-mono tracking-wide flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-purple-400" />
            SECURITY & SYSTEM AUDIT LOGS
          </h1>
          <p className="text-xs text-slate-400 font-mono">
            Immutable audit record foundation for logins, access changes, user management, and administrative events.
          </p>
        </div>

        <Button variant="outline" onClick={fetchLogs} isLoading={loading}>
          <RefreshCw className="w-4 h-4 mr-1" />
          Refresh Logs
        </Button>
      </div>

      {/* Filter Toolbar */}
      <Card>
        <form onSubmit={handleFilterSubmit} className="flex flex-col md:flex-row items-end gap-4">
          <div className="flex-1 w-full">
            <Input
              label="Filter by Actor Email"
              placeholder="Search by email..."
              value={emailFilter}
              onChange={(e) => setEmailFilter(e.target.value)}
            />
          </div>

          <div className="w-full md:w-64 space-y-1.5">
            <label className="block text-xs font-semibold text-slate-300 tracking-wide uppercase font-mono">
              Action Event Type
            </label>
            <select
              value={actionFilter}
              onChange={(e) => setActionFilter(e.target.value)}
              className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3.5 py-2 text-sm text-slate-100 font-mono focus:outline-none focus:border-cyan-500"
            >
              <option value="">All Action Events</option>
              <option value="LOGIN_SUCCESS">LOGIN_SUCCESS</option>
              <option value="LOGIN_FAILED">LOGIN_FAILED</option>
              <option value="LOGOUT">LOGOUT</option>
              <option value="PROFILE_UPDATE">PROFILE_UPDATE</option>
              <option value="PASSWORD_CHANGE_SUCCESS">PASSWORD_CHANGE_SUCCESS</option>
              <option value="USER_CREATED">USER_CREATED</option>
              <option value="ROLE_CHANGE">ROLE_CHANGE</option>
              <option value="USER_STATUS_CHANGE">USER_STATUS_CHANGE</option>
            </select>
          </div>

          <Button type="submit" variant="secondary">
            <Filter className="w-4 h-4 mr-1" />
            Apply Filters
          </Button>
        </form>
      </Card>

      {/* Audit Log Table */}
      <Card className="p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-900/80 text-[11px] font-mono uppercase tracking-wider text-slate-400">
                <th className="p-4">Timestamp (UTC)</th>
                <th className="p-4">Action Event</th>
                <th className="p-4">Actor Email</th>
                <th className="p-4">IP Address</th>
                <th className="p-4">Event Metadata</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-sm">
              {loading ? (
                <tr>
                  <td colSpan={5} className="p-8 text-center text-slate-500 font-mono">
                    Loading audit log history...
                  </td>
                </tr>
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan={5} className="p-8 text-center text-slate-500 font-mono">
                    No matching audit logs found.
                  </td>
                </tr>
              ) : (
                logs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-900/40 transition-colors font-mono text-xs">
                    <td className="p-4 text-slate-400 flex items-center gap-1.5 whitespace-nowrap">
                      <Clock className="w-3.5 h-3.5 text-slate-500" />
                      {new Date(log.created_at).toLocaleString()}
                    </td>
                    <td className="p-4">
                      <Badge variant={getActionBadgeVariant(log.action)}>
                        {log.action}
                      </Badge>
                    </td>
                    <td className="p-4 text-slate-200">
                      {log.actor_email || `ID: ${log.actor_id || 'System/Anon'}`}
                    </td>
                    <td className="p-4 text-slate-400">
                      {log.ip_address || '—'}
                    </td>
                    <td className="p-4 text-slate-400 max-w-md truncate">
                      {log.metadata_json ? JSON.stringify(log.metadata_json) : '—'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};
