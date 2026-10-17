import React from 'react';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { NetworkRiskRecord, StationConnections, DelayImpactRecord } from '../../services/mlService';
import { ShieldAlert, Activity, Info, GitFork } from 'lucide-react';

interface StationIntelligencePanelProps {
  stationRisk: NetworkRiskRecord | null;
  connections: StationConnections | null;
  delays: DelayImpactRecord[];
  onClose?: () => void;
}

export const StationIntelligencePanel: React.FC<StationIntelligencePanelProps> = ({
  stationRisk,
  connections,
  delays,
  onClose
}) => {
  if (!stationRisk && !connections) {
    return (
      <Card className="border-[#DDD9CF] bg-[#F7F5EF] text-center py-12 font-sans shadow-sm">
        <Info className="w-8 h-8 text-[#6F8F87] mx-auto mb-2 opacity-60" />
        <div className="text-[#29322F] font-semibold text-sm">Station Intelligence Panel</div>
        <div className="text-[#6F8F87] text-xs mt-1">Select a station node on the network map to inspect real-time metrics & advisory actions.</div>
      </Card>
    );
  }

  const stationName = stationRisk?.station_complex || connections?.station_complex || 'Selected Hub';
  const riskLevel = stationRisk?.network_risk || 'LOW';

  const getBadgeVariant = (risk: string) => {
    switch (risk?.toUpperCase()) {
      case 'CRITICAL': return 'rose';
      case 'HIGH': return 'amber';
      case 'MODERATE': return 'amber';
      default: return 'emerald';
    }
  };

  return (
    <Card className="space-y-6 border-[#DDD9CF] bg-white shadow-sm">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-4 border-b border-[#DDD9CF]">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-base font-bold font-sans text-[#29322F] tracking-wide">
              {stationName}
            </h3>
            <Badge variant={getBadgeVariant(riskLevel)}>
              Network Risk: {riskLevel}
            </Badge>
          </div>
          <div className="text-xs text-[#6F8F87] font-sans mt-1 flex flex-wrap gap-2">
            <span>Complex ID: {stationRisk?.station_complex_id || connections?.station_complex_id}</span>
            <span>•</span>
            <span>Serving Routes: {connections?.routes?.join(', ') || 'MTA Subway Lines'}</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 font-sans text-xs">
        <div className="p-3 rounded-xl bg-[#F7F5EF] border border-[#DDD9CF] space-y-1 shadow-sm">
          <div className="text-[10px] text-[#6F8F87] uppercase flex items-center justify-between font-semibold">
            <span>Historical Baseline</span>
            <Badge variant="emerald" size="sm">BASELINE</Badge>
          </div>
          <div className="text-lg font-bold text-[#29322F]">
            {stationRisk ? `${Math.round(stationRisk.predicted_next_hour * 0.95).toLocaleString()} / hr` : 'N/A'}
          </div>
          <div className="text-[10px] text-[#6F8F87]">Expected Turnstile Entries</div>
        </div>

        <div className="p-3 rounded-xl bg-[#F7F5EF] border border-[#DDD9CF] space-y-1 shadow-sm">
          <div className="text-[10px] text-[#6F8F87] uppercase flex items-center justify-between font-semibold">
            <span>Forecast Demand</span>
            <Badge variant="cyan" size="sm">PREDICTED</Badge>
          </div>
          <div className="text-lg font-bold text-[#2F6F68]">
            {stationRisk ? `${Math.round(stationRisk.predicted_next_hour).toLocaleString()} / hr` : 'N/A'}
          </div>
          <div className="text-[10px] text-[#6F8F87]">Demand Forecasting Model</div>
        </div>

        <div className="p-3 rounded-xl bg-[#F7F5EF] border border-[#DDD9CF] space-y-1 shadow-sm">
          <div className="text-[10px] text-[#6F8F87] uppercase flex items-center justify-between font-semibold">
            <span>Neighbor Transfer Load</span>
            <Badge variant="purple" size="sm">NETWORK</Badge>
          </div>
          <div className="text-lg font-bold text-[#29322F]">
            {stationRisk ? `${Math.round(stationRisk.neighbor_predicted_demand).toLocaleString()} / hr` : 'N/A'}
          </div>
          <div className="text-[10px] text-[#6F8F87]">
            Ratio: {stationRisk?.network_pressure_ratio.toFixed(2)}x Baseline
          </div>
        </div>
      </div>

      {connections && connections.neighbors.length > 0 && (
        <div className="space-y-2 font-sans">
          <div className="text-xs uppercase tracking-wider text-[#6F8F87] font-semibold flex items-center gap-1.5">
            <GitFork className="w-3.5 h-3.5 text-[#2F6F68]" />
            Connected Station Neighbors ({connections.neighbors.length}):
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-2 text-xs">
            {connections.neighbors.map((nbr, idx) => (
              <div key={idx} className="p-2.5 rounded-lg bg-[#F7F5EF] border border-[#DDD9CF] flex items-center justify-between shadow-sm">
                <div>
                  <div className="text-[#29322F] font-semibold text-[11px]">{nbr.name}</div>
                  <div className="text-[10px] text-[#6F8F87]">Routes: {nbr.routes.join(', ')}</div>
                </div>
                {nbr.transfer_hub && (
                  <Badge variant="purple" size="sm">Transfer Hub</Badge>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {stationRisk?.contributing_factors && stationRisk.contributing_factors.length > 0 && (
        <div className="space-y-2 font-sans">
          <div className="text-xs uppercase tracking-wider text-[#6F8F87] font-semibold flex items-center gap-1.5">
            <Activity className="w-3.5 h-3.5 text-[#2F6F68]" />
            Contributing Risk Factors:
          </div>
          <div className="space-y-1.5 text-xs">
            {stationRisk.contributing_factors.map((factor, idx) => (
              <div key={idx} className="p-2 rounded-lg bg-[#F7F5EF] border border-[#DDD9CF] flex items-center gap-2 text-[#29322F]">
                <span className="w-1.5 h-1.5 rounded-full bg-[#2F6F68]"></span>
                <span>{factor}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="p-4 rounded-xl bg-[#F7F5EF] border border-[#DDD9CF] space-y-2 font-sans shadow-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-[#29322F] font-semibold text-xs uppercase tracking-wide">
            <ShieldAlert className="w-4 h-4 text-[#2F6F68]" />
            Operator Advisory Recommendation:
          </div>
          <Badge variant="cyan" size="sm">HUMAN-IN-THE-LOOP ADVISORY</Badge>
        </div>
        <p className="text-xs text-[#6F8F87] leading-relaxed">
          {stationRisk?.recommended_action || "Normal monitoring across station complex platform areas."}
        </p>
      </div>
    </Card>
  );
};
