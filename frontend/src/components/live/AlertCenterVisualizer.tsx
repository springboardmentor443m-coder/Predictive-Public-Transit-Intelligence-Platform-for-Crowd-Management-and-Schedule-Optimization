import React, { useState } from 'react';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { Button } from '../common/Button';
import { OperationalAlert, AlertSummary, alertService } from '../../services/alertService';
import {
  Bell,
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Filter,
  Search,
  Check,
  Zap,
  Info,
  ChevronRight,
  X,
  Radio,
  Sparkles
} from 'lucide-react';

interface AlertCenterVisualizerProps {
  alerts: OperationalAlert[];
  history: OperationalAlert[];
  summary: AlertSummary | null;
  onRefresh: () => void;
}

export const AlertCenterVisualizer: React.FC<AlertCenterVisualizerProps> = ({
  alerts,
  history,
  summary,
  onRefresh
}) => {
  const [activeTab, setActiveTab] = useState<'active' | 'history'>('active');
  const [severityFilter, setSeverityFilter] = useState<string>('ALL');
  const [typeFilter, setTypeFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedAlert, setSelectedAlert] = useState<OperationalAlert | null>(null);
  const [ackLoadingId, setAckLoadingId] = useState<number | null>(null);

  const handleAcknowledge = async (alertId: number) => {
    setAckLoadingId(alertId);
    try {
      await alertService.acknowledgeAlert(alertId, "Operator reviewed alert from Operations Dashboard.");
      onRefresh();
      if (selectedAlert && selectedAlert.id === alertId) {
        setSelectedAlert((prev: OperationalAlert | null) => (prev ? { ...prev, status: 'ACKNOWLEDGED' } : null));
      }
    } catch (err) {
      console.error("Failed to acknowledge alert:", err);
    } finally {
      setAckLoadingId(null);
    }
  };

  const getSeverityBadge = (severity: string) => {
    switch (severity.toUpperCase()) {
      case 'CRITICAL':
        return <Badge variant="rose">CRITICAL</Badge>;
      case 'HIGH':
        return <Badge variant="amber">HIGH</Badge>;
      case 'WARNING':
        return <Badge variant="amber">WARNING</Badge>;
      default:
        return <Badge variant="cyan">INFO</Badge>;
    }
  };

  const getTypeBadge = (type: string) => {
    switch (type.toUpperCase()) {
      case 'OVERCROWDING':
        return <Badge variant="purple">PREDICTED CROWD RISK</Badge>;
      case 'LIVE_DELAY':
        return <Badge variant="cyan">LIVE GTFS-RT DELAY</Badge>;
      case 'SERVICE_ALERT':
        return <Badge variant="amber">MTA BULLETIN</Badge>;
      case 'NETWORK_IMPACT':
        return <Badge variant="purple">NETWORK CONGESTION</Badge>;
      default:
        return <Badge variant="slate">{type}</Badge>;
    }
  };

  const currentList = activeTab === 'active' ? alerts : history;

  const filteredAlerts = currentList.filter((alt) => {
    const matchesSev = severityFilter === 'ALL' || alt.severity.toUpperCase() === severityFilter;
    const matchesType = typeFilter === 'ALL' || alt.alert_type.toUpperCase() === typeFilter;
    const matchesQuery =
      alt.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      alt.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (alt.entity_name && alt.entity_name.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesSev && matchesType && matchesQuery;
  });

  return (
    <div className="space-y-6 font-sans">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="flex items-center gap-4 border-[#DDD9CF] shadow-sm bg-white">
          <div className="p-3 rounded-xl bg-[#F7F5EF] border border-[#DDD9CF] text-[#2F6F68]">
            <Bell className="w-6 h-6" />
          </div>
          <div>
            <div className="text-[11px] text-[#6F8F87] uppercase font-semibold">Active Alerts</div>
            <div className="text-xl font-bold text-[#29322F]">{summary?.total_active ?? 0}</div>
            <div className="text-[10px] text-[#2F6F68]">
              {summary?.overcrowding_count ?? 0} Crowd • {summary?.live_delays_count ?? 0} Delays
            </div>
          </div>
        </Card>

        <Card className="flex items-center gap-4 border-[#DDD9CF] shadow-sm bg-white">
          <div className="p-3 rounded-xl bg-[#B9574B]/10 border border-[#B9574B]/20 text-[#B9574B]">
            <ShieldAlert className="w-6 h-6" />
          </div>
          <div>
            <div className="text-[11px] text-[#6F8F87] uppercase font-semibold">Critical Severity</div>
            <div className="text-xl font-bold text-[#B9574B]">{summary?.critical_count ?? 0}</div>
            <div className="text-[10px] text-[#B9574B]">Requires Immediate Review</div>
          </div>
        </Card>

        <Card className="flex items-center gap-4 border-[#DDD9CF] shadow-sm bg-white">
          <div className="p-3 rounded-xl bg-[#C58A3A]/10 border border-[#C58A3A]/20 text-[#C58A3A]">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <div>
            <div className="text-[11px] text-[#6F8F87] uppercase font-semibold">High Priority</div>
            <div className="text-xl font-bold text-[#C58A3A]">{summary?.high_count ?? 0}</div>
            <div className="text-[10px] text-[#C58A3A]">High Risk & Congestion</div>
          </div>
        </Card>

        <Card className="flex items-center gap-4 border-[#DDD9CF] shadow-sm bg-white">
          <div className="p-3 rounded-xl bg-[#F7F5EF] border border-[#DDD9CF] text-[#6F8F87]">
            <Radio className="w-6 h-6" />
          </div>
          <div>
            <div className="text-[11px] text-[#6F8F87] uppercase font-semibold">Telemetry Delays</div>
            <div className="text-xl font-bold text-[#29322F]">{summary?.live_delays_count ?? 0} Line Delays</div>
            <div className="text-[10px] text-[#6F8F87]">Real-Time Ingestion Active</div>
          </div>
        </Card>
      </div>

      <Card className="space-y-4 border-[#DDD9CF] shadow-sm bg-white">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-3 border-b border-[#DDD9CF]">
          <div className="flex items-center gap-2">
            <Bell className="w-5 h-5 text-[#2F6F68]" />
            <h2 className="text-sm font-bold text-[#29322F] uppercase tracking-wide">
              OPERATIONAL ALERT CENTER
            </h2>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant={activeTab === 'active' ? 'primary' : 'outline'}
              size="sm"
              onClick={() => setActiveTab('active')}
            >
              Active Alerts ({alerts.length})
            </Button>
            <Button
              variant={activeTab === 'history' ? 'primary' : 'outline'}
              size="sm"
              onClick={() => setActiveTab('history')}
            >
              History ({history.length})
            </Button>
          </div>
        </div>

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 p-3 rounded-xl bg-[#F7F5EF] border border-[#DDD9CF]">
          <div className="flex items-center gap-2 flex-1">
            <div className="relative flex-1 max-w-xs">
              <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-[#6F8F87]" />
              <input
                type="text"
                placeholder="Search alerts..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-white border border-[#DDD9CF] rounded-lg pl-8 pr-3 py-1.5 text-xs text-[#29322F] focus:outline-none focus:border-[#2F6F68]"
              />
            </div>

            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="bg-white border border-[#DDD9CF] rounded-lg px-3 py-1.5 text-xs text-[#29322F] focus:outline-none focus:border-[#2F6F68]"
            >
              <option value="ALL">All Severities</option>
              <option value="CRITICAL">CRITICAL</option>
              <option value="HIGH">HIGH</option>
              <option value="WARNING">WARNING</option>
              <option value="INFO">INFO</option>
            </select>

            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="bg-white border border-[#DDD9CF] rounded-lg px-3 py-1.5 text-xs text-[#29322F] focus:outline-none focus:border-[#2F6F68]"
            >
              <option value="ALL">All Types</option>
              <option value="SERVICE_ALERT">MTA Service Bulletins</option>
              <option value="LIVE_DELAY">Live GTFS-RT Delay</option>
              <option value="OVERCROWDING">Predicted Crowd Risk</option>
              <option value="NETWORK_IMPACT">Network Congestion</option>
            </select>
          </div>

          <div className="text-[11px] text-[#6F8F87]">
            Showing <span className="text-[#2F6F68] font-bold">{filteredAlerts.length}</span> items
          </div>
        </div>

        {filteredAlerts.length === 0 ? (
          <div className="p-8 rounded-xl bg-[#F7F5EF] border border-[#DDD9CF] text-center space-y-3">
            <CheckCircle2 className="w-10 h-10 text-[#4F8A63] mx-auto" />
            <div className="text-[#29322F] font-bold text-sm">NO ACTIVE ALERTS DETECTED</div>
            <p className="text-xs text-[#6F8F87] max-w-md mx-auto">
              {activeTab === 'active'
                ? 'System is operating nominally.'
                : 'No alert history records match the criteria.'}
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredAlerts.map((alert) => (
              <div
                key={alert.id}
                className={`p-4 rounded-xl border transition-all ${
                  alert.severity === 'CRITICAL'
                    ? 'bg-[#B9574B]/5 border-[#B9574B]/30 hover:border-[#B9574B]/60'
                    : alert.severity === 'HIGH'
                    ? 'bg-[#C58A3A]/5 border-[#C58A3A]/30 hover:border-[#C58A3A]/60'
                    : 'bg-white border-[#DDD9CF] hover:border-[#2F6F68]/50'
                }`}
              >
                <div className="flex flex-col md:flex-row md:items-start justify-between gap-3">
                  <div className="space-y-2 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      {getSeverityBadge(alert.severity)}
                      {getTypeBadge(alert.alert_type)}
                      <Badge variant={alert.data_state === 'LIVE' ? 'cyan' : 'purple'}>
                        {alert.data_state}
                      </Badge>
                      <span className="text-[10px] text-[#6F8F87] font-sans font-medium">
                        {new Date(alert.timestamp).toLocaleTimeString()}
                      </span>
                    </div>

                    <h3 className="text-sm font-bold text-[#29322F] leading-snug">{alert.title}</h3>
                    <p className="text-xs text-[#6F8F87] leading-relaxed max-w-3xl">{alert.description}</p>

                    {alert.recommended_action && (
                      <div className="p-2.5 rounded-lg bg-[#F7F5EF] border border-[#DDD9CF] text-xs text-[#29322F] flex items-start gap-2 shadow-sm">
                        <Sparkles className="w-4 h-4 text-[#2F6F68] shrink-0 mt-0.5" />
                        <div>
                          <span className="font-bold text-[#2F6F68]">Operator Advisory Action: </span>
                          <span>{alert.recommended_action}</span>
                        </div>
                      </div>
                    )}
                  </div>

                  <div className="flex md:flex-col items-center md:items-end justify-between gap-3 shrink-0 pt-2 md:pt-0 border-t md:border-t-0 border-[#DDD9CF]">
                    {alert.status === 'ACKNOWLEDGED' ? (
                      <div className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-[#4F8A63]/10 border border-[#4F8A63]/20 text-[#4F8A63] text-xs font-bold">
                        <Check className="w-3.5 h-3.5" />
                        <span>ACKNOWLEDGED</span>
                      </div>
                    ) : alert.status === 'RESOLVED' ? (
                      <div className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-[#F7F5EF] border border-[#DDD9CF] text-[#6F8F87] text-xs font-bold">
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>RESOLVED</span>
                      </div>
                    ) : (
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={() => handleAcknowledge(alert.id)}
                        isLoading={ackLoadingId === alert.id}
                      >
                        <Check className="w-3.5 h-3.5 mr-1" />
                        Acknowledge
                      </Button>
                    )}

                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setSelectedAlert(alert)}
                    >
                      Detail <ChevronRight className="w-3.5 h-3.5 ml-1" />
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      {selectedAlert && (
        <div className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white border border-[#DDD9CF] rounded-2xl max-w-2xl w-full p-6 space-y-5 text-xs font-sans shadow-2xl relative">
            <button
              onClick={() => setSelectedAlert(null)}
              className="absolute top-4 right-4 text-[#6F8F87] hover:text-[#29322F] p-1"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-2">
              {getSeverityBadge(selectedAlert.severity)}
              {getTypeBadge(selectedAlert.alert_type)}
            </div>

            <div>
              <h2 className="text-base font-bold text-[#29322F]">{selectedAlert.title}</h2>
            </div>

            <div className="p-4 rounded-xl bg-[#F7F5EF] border border-[#DDD9CF] space-y-3">
              <div>
                <span className="text-[#6F8F87] block font-bold text-[11px] uppercase">Description</span>
                <p className="text-[#29322F] text-xs mt-1 leading-relaxed">{selectedAlert.description}</p>
              </div>

              <div className="grid grid-cols-2 gap-3 pt-2 border-t border-[#DDD9CF] text-[11px]">
                <div>
                  <span className="text-[#6F8F87]">Target Entity:</span>
                  <span className="text-[#29322F] block font-semibold">{selectedAlert.entity_name || selectedAlert.entity_id || 'System'}</span>
                </div>

                <div>
                  <span className="text-[#6F8F87]">Observed Value:</span>
                  <span className="text-[#29322F] block font-semibold">{selectedAlert.observed_value || 'None'}</span>
                </div>
              </div>
            </div>

            {selectedAlert.recommended_action && (
              <div className="p-3.5 rounded-xl bg-[#F7F5EF] border border-[#DDD9CF] space-y-1">
                <div className="flex items-center gap-1.5 font-bold text-[#2F6F68] text-xs">
                  <Sparkles className="w-4 h-4 text-[#2F6F68]" />
                  <span>RECOMMENDED ACTION</span>
                </div>
                <p className="text-[#29322F] leading-relaxed text-xs">{selectedAlert.recommended_action}</p>
              </div>
            )}

            <div className="flex items-center justify-between pt-3 border-t border-[#DDD9CF]">
              <div className="text-[10px] text-[#6F8F87]">
                Timestamp: {new Date(selectedAlert.timestamp).toLocaleString()}
              </div>

              {selectedAlert.status === 'ACTIVE' && (
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => handleAcknowledge(selectedAlert.id)}
                  isLoading={ackLoadingId === selectedAlert.id}
                >
                  <Check className="w-3.5 h-3.5 mr-1" />
                  Acknowledge Alert
                </Button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
