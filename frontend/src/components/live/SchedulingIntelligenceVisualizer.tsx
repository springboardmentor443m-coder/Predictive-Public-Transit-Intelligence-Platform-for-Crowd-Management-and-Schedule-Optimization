import React from 'react';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { SchedulingIntelligenceRecord } from '../../services/mlService';
import { Calendar, Info, Sparkles } from 'lucide-react';

interface SchedulingIntelligenceVisualizerProps {
  records: SchedulingIntelligenceRecord[];
}

export const SchedulingIntelligenceVisualizer: React.FC<SchedulingIntelligenceVisualizerProps> = ({ records }) => {
  const getTierBadge = (tier: string) => {
    switch (tier?.toUpperCase()) {
      case 'URGENT_OPERATIONAL_ADVISORY':
        return <Badge variant="rose">URGENT ADVISORY</Badge>;
      case 'HIGH_PRIORITY':
        return <Badge variant="amber">HIGH PRIORITY</Badge>;
      case 'STANDARD_OPERATIONS':
        return <Badge variant="cyan">STANDARD FREQUENCY</Badge>;
      default:
        return <Badge variant="emerald">SYSTEM NORMAL</Badge>;
    }
  };

  return (
    <Card className="space-y-4 border-[#DDD9CF] shadow-sm bg-white">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-3 border-b border-[#DDD9CF]">
        <div className="flex items-center gap-2">
          <Calendar className="w-5 h-5 text-[#2F6F68]" />
          <h3 className="text-sm font-bold font-sans text-[#29322F] tracking-wide">
            Dynamic Scheduling & Service Advisories
          </h3>
        </div>
        <div className="flex items-center gap-2 font-sans text-[11px]">
          <Badge variant="purple">LIVE TELEMETRY</Badge>
          <Badge variant="cyan">DECISION SUPPORT</Badge>
        </div>
      </div>

      <div className="p-3 rounded-lg bg-[#F7F5EF] border border-[#DDD9CF] flex items-start gap-3 font-sans text-xs text-[#6F8F87]">
        <Info className="w-4 h-4 text-[#2F6F68] shrink-0 mt-0.5" />
        <div>
          <span className="font-bold text-[#29322F]">OPERATOR ADVISORY ONLY: </span>
          <span>
            MetroFlow outputs dynamic headway recommendations balancing current live delays and passenger demand pressure. All recommendations are advisories for dispatcher review and do not automatically alter signals or vehicle operations.
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 font-sans text-xs">
        {records.slice(0, 9).map((record) => {
          return (
            <div
              key={record.station_complex_id}
              className="p-4 rounded-xl bg-white border border-[#DDD9CF] shadow-sm flex flex-col justify-between space-y-3 hover:border-[#2F6F68]/50 transition-colors"
            >
              <div className="flex items-start justify-between gap-2">
                <div>
                  <h4 className="text-[#29322F] font-bold text-sm">{record.station_complex}</h4>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {record.routes.map((rt) => (
                      <span
                        key={rt}
                        className="px-1.5 py-0.5 rounded bg-[#F7F5EF] border border-[#DDD9CF] text-[10px] text-[#29322F] font-bold"
                      >
                        Line {rt}
                      </span>
                    ))}
                  </div>
                </div>
                {getTierBadge(record.advisory_tier)}
              </div>

              <div className="p-2.5 rounded-lg bg-[#F7F5EF]/50 border border-[#DDD9CF]/50 space-y-2">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-[#6F8F87]">Demand Pressure:</span>
                  <span className={`font-bold ${record.demand_pressure_ratio >= 1.2 ? 'text-[#C58A3A]' : 'text-[#4F8A63]'}`}>
                    {record.demand_pressure_ratio}x baseline
                  </span>
                </div>
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-[#6F8F87]">Live Headway:</span>
                  <span className={`font-bold ${record.current_headway_minutes > 15 ? 'text-[#B9574B]' : 'text-[#4F8A63]'}`}>
                    {record.current_headway_minutes > 0 ? `${record.current_headway_minutes}m` : 'Unknown'}
                  </span>
                </div>
                <div className="flex items-center justify-between text-[11px] pt-1 border-t border-[#DDD9CF]">
                  <span className="text-[#6F8F87]">Suggested Headway:</span>
                  <span className="text-[#29322F] font-semibold">
                    {record.recommended_headway_minutes}m
                  </span>
                </div>
              </div>

              <div className="space-y-1">
                <div className="flex items-center gap-1.5 text-[11px] text-[#29322F] font-semibold">
                  <Sparkles className="w-3.5 h-3.5 text-[#2F6F68] shrink-0" />
                  <span>Advisory Summary:</span>
                </div>
                <p className="text-[11px] text-[#6F8F87] leading-relaxed bg-[#F7F5EF] p-2 rounded border border-[#DDD9CF]/60">
                  {record.recommended_action}
                </p>
              </div>

              <div className="text-[10px] text-[#6F8F87] pt-1 border-t border-[#DDD9CF] flex items-center justify-between">
                <span>State: {record.data_state}</span>
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
};
