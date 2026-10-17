import React, { useState } from 'react';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { NetworkRiskRecord, StationConnections } from '../../services/mlService';
import { Network } from 'lucide-react';

interface NetworkTopologyVisualizerProps {
  networkRisks: NetworkRiskRecord[];
  selectedStationId: string | null;
  onSelectStation: (stationId: string, stationName: string) => void;
  connectionsDetail?: StationConnections | null;
}

export const NetworkTopologyVisualizer: React.FC<NetworkTopologyVisualizerProps> = ({
  networkRisks,
  selectedStationId,
  onSelectStation,
  connectionsDetail
}) => {
  const nodePositions: Record<string, { x: number; y: number; name: string; shortName: string }> = {
    "164": { x: 270, y: 220, name: "34 St-Penn (A,C,E)", shortName: "Penn (ACE)" },
    "318": { x: 350, y: 270, name: "34 St-Penn (1,2,3)", shortName: "Penn (123)" },
    "447": { x: 880, y: 120, name: "Flushing-Main St (7)", shortName: "Flushing (7)" },
    "601": { x: 290, y: 380, name: "14 St / 6 Av", shortName: "14 St-6 Av" },
    "602": { x: 440, y: 390, name: "14 St-Union Sq", shortName: "Union Sq" },
    "607": { x: 450, y: 250, name: "34 St-Herald Sq", shortName: "Herald Sq" },
    "610": { x: 590, y: 200, name: "Grand Central-42 St", shortName: "Grand Central" },
    "611": { x: 440, y: 160, name: "Times Sq-42 St", shortName: "Times Sq" },
    "614": { x: 380, y: 70,  name: "59 St-Columbus Cir", shortName: "Columbus Cir" },
    "616": { x: 740, y: 150, name: "Roosevelt Av", shortName: "Roosevelt Av" },
    "624": { x: 230, y: 470, name: "Chambers St / WTC", shortName: "Chambers/WTC" },
    "628": { x: 370, y: 480, name: "Fulton St", shortName: "Fulton St" }
  };

  const edges: Array<[string, string]> = [
    ["164", "611"], ["164", "624"], ["318", "611"], ["318", "601"],
    ["447", "616"], ["447", "610"], ["601", "607"], ["601", "602"],
    ["602", "607"], ["602", "610"], ["602", "628"], ["607", "611"],
    ["610", "611"], ["611", "614"], ["616", "610"], ["624", "628"]
  ];

  const getRiskColor = (risk: string) => {
    switch (risk?.toUpperCase()) {
      case 'CRITICAL':
        return { fill: '#B9574B', stroke: '#8c4239', bg: 'bg-[#B9574B]/20', text: 'text-[#B9574B]' };
      case 'HIGH':
        return { fill: '#C58A3A', stroke: '#966a2c', bg: 'bg-[#C58A3A]/20', text: 'text-[#C58A3A]' };
      case 'MODERATE':
        return { fill: '#eab308', stroke: '#ca8a04', bg: 'bg-yellow-100', text: 'text-yellow-700' };
      default:
        return { fill: '#4F8A63', stroke: '#3a6649', bg: 'bg-[#4F8A63]/20', text: 'text-[#4F8A63]' };
    }
  };

  const riskLookup = React.useMemo(() => {
    const map: Record<string, NetworkRiskRecord> = {};
    networkRisks.forEach(r => {
      map[r.station_complex_id] = r;
    });
    return map;
  }, [networkRisks]);

  return (
    <Card className="space-y-6 border-[#DDD9CF] shadow-sm bg-white">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-[#DDD9CF]">
        <div>
          <div className="flex items-center gap-2">
            <Network className="w-5 h-5 text-[#2F6F68]" />
            <h2 className="text-base font-bold font-sans tracking-wide text-[#29322F] uppercase">
              Connected Station Topology
            </h2>
          </div>
          <p className="text-xs text-[#6F8F87] font-sans mt-1">
            Topological graph of major NYC transit hubs representing spatial demand pressure & connected line risk.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2 font-sans text-[11px]">
          <Badge variant="cyan">LIVE: Telemetry</Badge>
          <Badge variant="purple">PREDICTED: Network Impact</Badge>
          <Badge variant="emerald">OBSERVED: Turnstile</Badge>
        </div>
      </div>

      <div className="relative bg-[#F7F5EF] rounded-xl border border-[#DDD9CF] p-4 overflow-hidden shadow-inner">
        <svg viewBox="0 0 1000 520" className="w-full h-auto max-h-[460px]">
          {edges.map(([fromId, toId], idx) => {
            const p1 = nodePositions[fromId];
            const p2 = nodePositions[toId];
            if (!p1 || !p2) return null;

            const r1 = riskLookup[fromId]?.network_risk;
            const r2 = riskLookup[toId]?.network_risk;
            const isHighRiskEdge = r1 === 'CRITICAL' || r2 === 'CRITICAL' || r1 === 'HIGH' || r2 === 'HIGH';

            return (
              <line
                key={idx}
                x1={p1.x}
                y1={p1.y}
                x2={p2.x}
                y2={p2.y}
                stroke={isHighRiskEdge ? '#C58A3A' : '#A9B4AE'}
                strokeWidth={isHighRiskEdge ? 2.5 : 1.5}
                strokeDasharray={isHighRiskEdge ? "4 4" : "none"}
                className={isHighRiskEdge ? "animate-pulse" : ""}
                opacity={0.8}
              />
            );
          })}

          {Object.entries(nodePositions).map(([stId, pos]) => {
            const riskRecord = riskLookup[stId];
            const riskLevel = riskRecord?.network_risk || 'LOW';
            const colors = getRiskColor(riskLevel);
            const isSelected = selectedStationId === stId;

            return (
              <g
                key={stId}
                className="cursor-pointer transition-all duration-200"
                onClick={() => onSelectStation(stId, pos.name)}
              >
                {isSelected && (
                  <circle
                    cx={pos.x}
                    cy={pos.y}
                    r={22}
                    fill="none"
                    stroke="#2F6F68"
                    strokeWidth={2}
                    className="animate-ping opacity-75"
                  />
                )}

                <circle
                  cx={pos.x}
                  cy={pos.y}
                  r={isSelected ? 16 : 12}
                  fill={colors.fill}
                  stroke={colors.stroke}
                  strokeWidth={2}
                  className="shadow-sm drop-shadow-sm"
                />

                <rect
                  x={pos.x - 70}
                  y={pos.y + 16}
                  width={140}
                  height={22}
                  rx={4}
                  fill="#ffffff"
                  stroke={isSelected ? '#2F6F68' : '#DDD9CF'}
                  strokeWidth={1}
                  opacity={0.9}
                  className="shadow-sm drop-shadow-sm"
                />

                <text
                  x={pos.x}
                  y={pos.y + 31}
                  textAnchor="middle"
                  fill="#29322F"
                  fontSize={10}
                  fontWeight="bold"
                  fontFamily="Inter, sans-serif"
                >
                  {pos.shortName} ({riskLevel[0]})
                </text>
              </g>
            );
          })}
        </svg>

        <div className="absolute bottom-3 left-3 bg-white border border-[#DDD9CF] p-2.5 rounded-lg shadow-sm text-[10px] font-sans space-y-1">
          <div className="text-[#6F8F87] font-semibold mb-1 uppercase">Node Congestion Risk:</div>
          <div className="flex items-center gap-3">
            <span className="flex items-center gap-1 text-[#4F8A63]"><span className="w-2 h-2 rounded-full bg-[#4F8A63]"></span> LOW</span>
            <span className="flex items-center gap-1 text-yellow-600"><span className="w-2 h-2 rounded-full bg-yellow-500"></span> MOD</span>
            <span className="flex items-center gap-1 text-[#C58A3A]"><span className="w-2 h-2 rounded-full bg-[#C58A3A]"></span> HIGH</span>
            <span className="flex items-center gap-1 text-[#B9574B]"><span className="w-2 h-2 rounded-full bg-[#B9574B] animate-pulse"></span> CRIT</span>
          </div>
        </div>
      </div>
    </Card>
  );
};
