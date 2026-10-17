import React, { useState } from 'react';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';
import { Button } from '../common/Button';
import {
  TrafficAnalyticsResponse,
  RiskDistribution,
  FeatureImportance,
  MLSummary,
  MLStationStatus
} from '../../services/mlService';
import {
  BarChart2,
  TrendingUp,
  Clock,
  Calendar,
  Activity
} from 'lucide-react';

interface AnalyticsMatrixVisualizerProps {
  traffic: TrafficAnalyticsResponse | null;
  riskDist: RiskDistribution[];
  featureImportances: FeatureImportance[];
  summary: MLSummary | null;
  stations: MLStationStatus[];
}

export const AnalyticsMatrixVisualizer: React.FC<AnalyticsMatrixVisualizerProps> = ({
  traffic,
  riskDist,
  featureImportances,
  summary,
  stations
}) => {
  const [subTab, setSubTab] = useState<'traffic' | 'performance'>('traffic');

  const maxHourlyVal = traffic ? Math.max(...traffic.hourly_patterns.map((h) => Math.max(h.avg_passenger_count, h.predicted_avg_count))) : 3000;
  const maxWkdayVal = traffic ? Math.max(...traffic.weekday_patterns.map((w) => w.avg_passenger_count)) : 3500;

  return (
    <div className="space-y-6 font-sans">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 p-4 rounded-2xl border border-[#DDD9CF] bg-white shadow-sm">
        <div className="flex items-center gap-2">
          <BarChart2 className="w-5 h-5 text-[#2F6F68]" />
          <h2 className="text-sm font-bold text-[#29322F] uppercase tracking-wide">
            OPERATIONS ANALYTICS MATRIX
          </h2>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Button
            variant={subTab === 'traffic' ? 'primary' : 'outline'}
            size="sm"
            onClick={() => setSubTab('traffic')}
          >
            <TrendingUp className="w-4 h-4 mr-1.5" />
            Passenger Traffic
          </Button>

          <Button
            variant={subTab === 'performance' ? 'primary' : 'outline'}
            size="sm"
            onClick={() => setSubTab('performance')}
          >
            <Activity className="w-4 h-4 mr-1.5" />
            Station Performance
          </Button>

        </div>
      </div>

      {subTab === 'traffic' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card className="border-[#DDD9CF] bg-white shadow-sm">
              <div className="flex items-center justify-between pb-2 border-b border-[#DDD9CF]">
                <span className="text-[11px] text-[#6F8F87] font-semibold uppercase">Peak-Hour Demand Avg</span>
                <Badge variant="cyan">HISTORICAL</Badge>
              </div>
              <div className="mt-3">
                <div className="text-2xl font-bold text-[#29322F]">
                  {traffic ? `${Math.round(traffic.peak_summary.peak_hour_avg).toLocaleString()} pax/hr` : '---'}
                </div>
                <div className="text-[11px] text-[#6F8F87] mt-1">7-10 AM & 4-8 PM Commute Hours</div>
              </div>
            </Card>

            <Card className="border-[#DDD9CF] bg-white shadow-sm">
              <div className="flex items-center justify-between pb-2 border-b border-[#DDD9CF]">
                <span className="text-[11px] text-[#6F8F87] font-semibold uppercase">Off-Peak Demand Avg</span>
                <Badge variant="slate">HISTORICAL</Badge>
              </div>
              <div className="mt-3">
                <div className="text-2xl font-bold text-[#29322F]">
                  {traffic ? `${Math.round(traffic.peak_summary.off_peak_hour_avg).toLocaleString()} pax/hr` : '---'}
                </div>
                <div className="text-[11px] text-[#6F8F87] mt-1">Baseline Standard Dwell</div>
              </div>
            </Card>

            <Card className="border-[#DDD9CF] bg-white shadow-sm">
              <div className="flex items-center justify-between pb-2 border-b border-[#DDD9CF]">
                <span className="text-[11px] text-[#6F8F87] font-semibold uppercase">Peak Demand Multiplier</span>
                <Badge variant="purple">SURGE FACTOR</Badge>
              </div>
              <div className="mt-3">
                <div className="text-2xl font-bold text-[#2F6F68]">
                  {traffic ? `${traffic.peak_summary.peak_multiplier}x` : '---'}
                </div>
                <div className="text-[11px] text-[#6F8F87] mt-1">Surge Ratio vs Off-Peak Average</div>
              </div>
            </Card>

            <Card className="border-[#2F6F68]/30 bg-[#2F6F68]/5 shadow-sm">
              <div className="flex items-center justify-between pb-2 border-b border-[#DDD9CF]">
                <span className="text-[11px] text-[#2F6F68] font-bold uppercase flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-[#2F6F68] animate-pulse" />
                  Live System Load
                </span>
                <Badge variant={traffic?.peak_summary?.is_peak_now ? 'rose' : 'cyan'}>
                  {traffic?.peak_summary?.is_peak_now ? 'RUSH HOUR' : 'NOMINAL'}
                </Badge>
              </div>
              <div className="mt-3">
                <div className="text-2xl font-bold text-[#29322F]">
                  {traffic?.peak_summary?.live_system_load_ratio ? `${traffic.peak_summary.live_system_load_ratio}x` : '1.0x'}
                </div>
                <div className="text-[11px] text-[#6F8F87] mt-1">
                  {traffic?.peak_summary?.current_live_system_demand
                    ? `${Math.round(traffic.peak_summary.current_live_system_demand).toLocaleString()} pax live network forecast`
                    : 'Real-time ML demand inference'}
                </div>
              </div>
            </Card>
          </div>

          <Card className="space-y-4 border-[#DDD9CF] bg-white shadow-sm">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 pb-3 border-b border-[#DDD9CF]">
              <div className="flex items-center gap-2">
                <Clock className="w-5 h-5 text-[#2F6F68]" />
                <h3 className="text-sm font-bold text-[#29322F] uppercase tracking-wide">
                  24-Hour Diurnal Passenger Demand Curve
                </h3>
              </div>
              <div className="flex items-center gap-4 text-xs font-semibold">
                <div className="flex items-center gap-1.5">
                  <span className="w-3 h-3 rounded-sm bg-[#4F8A63] inline-block" />
                  <span className="text-[#6F8F87]">Historical Demand</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-3 h-3 rounded-sm bg-[#C58A3A] inline-block" />
                  <span className="text-[#6F8F87]">ML Forecast</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-[#2F6F68] animate-pulse inline-block" />
                  <span className="text-[#2F6F68]">Current Hour (Live)</span>
                </div>
              </div>
            </div>

            <div className="pt-4 pb-2">
              <div className="h-56 flex items-end gap-2 px-2 border-b border-[#DDD9CF]">
                {traffic?.hourly_patterns.map((item) => {
                  const obsHeight = Math.max(10, Math.round((item.avg_passenger_count / maxHourlyVal) * 100));
                  const predHeight = Math.max(10, Math.round((item.predicted_avg_count / maxHourlyVal) * 100));
                  const isPeak = [7, 8, 9, 16, 17, 18, 19].includes(item.hour);
                  const isCurrent = item.is_current_hour;

                  return (
                    <div key={item.hour} className={`flex-1 flex flex-col items-center gap-1 group relative h-full ${isCurrent ? 'bg-[#2F6F68]/10 rounded-t border-b-2 border-[#2F6F68]' : ''}`}>
                      <div className="absolute bottom-full mb-2 hidden group-hover:block z-20 bg-white border border-[#DDD9CF] p-2 rounded text-[10px] whitespace-nowrap shadow-xl">
                        <div className="font-bold text-[#29322F] flex items-center gap-1">
                          Hour {item.hour}:00
                          {isCurrent && <span className="text-[#2F6F68] font-bold">(CURRENT LIVE HOUR)</span>}
                        </div>
                        <div className="text-[#4F8A63]">Historical: {Math.round(item.avg_passenger_count).toLocaleString()} pax</div>
                        <div className="text-[#C58A3A]">Forecast: {Math.round(item.predicted_avg_count).toLocaleString()} pax</div>
                        {item.live_current_demand && (
                          <div className="text-[#2F6F68] font-semibold">Live Avg: {Math.round(item.live_current_demand).toLocaleString()} pax</div>
                        )}
                      </div>

                      <div className="w-full flex items-end justify-center gap-0.5 h-full">
                        <div
                          style={{ height: `${obsHeight}%` }}
                          className={`w-1/2 rounded-t transition-all ${isCurrent ? 'bg-[#2F6F68]' : isPeak ? 'bg-[#4F8A63]' : 'bg-[#4F8A63]/50'}`}
                        />
                        <div
                          style={{ height: `${predHeight}%` }}
                          className={`w-1/2 rounded-t transition-all ${isCurrent ? 'bg-[#C58A3A] ring-1 ring-[#2F6F68]' : 'bg-[#C58A3A]/80'}`}
                        />
                      </div>
                      <span className={`text-[10px] ${isCurrent ? 'text-[#2F6F68] font-black underline' : isPeak ? 'text-[#29322F] font-bold' : 'text-[#6F8F87]'}`}>
                        {item.hour}h
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          </Card>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="space-y-4 border-[#DDD9CF] bg-white shadow-sm">
              <div className="flex items-center justify-between pb-3 border-b border-[#DDD9CF]">
                <div className="flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-[#2F6F68]" />
                  <h3 className="text-sm font-bold text-[#29322F] uppercase">Day-of-Week Demand Profile</h3>
                </div>
              </div>

              <div className="space-y-3 pt-2">
                {traffic?.weekday_patterns.map((item) => {
                  const pct = Math.round((item.avg_passenger_count / maxWkdayVal) * 100);
                  const isWeekend = ['Saturday', 'Sunday'].includes(item.day);

                  return (
                    <div key={item.day} className="space-y-1 text-xs">
                      <div className="flex items-center justify-between">
                        <span className={`font-semibold ${isWeekend ? 'text-[#6F8F87]' : 'text-[#29322F]'}`}>
                          {item.day}
                        </span>
                        <span className="text-[#6F8F87] font-bold">
                          {Math.round(item.avg_passenger_count).toLocaleString()} pax/hr
                        </span>
                      </div>
                      <div className="w-full bg-[#F7F5EF] rounded-full h-2 overflow-hidden border border-[#DDD9CF]">
                        <div
                          style={{ width: `${pct}%` }}
                          className={`h-full rounded-full transition-all ${isWeekend ? 'bg-[#C58A3A]/60' : 'bg-[#2F6F68]'}`}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </Card>

            <Card className="space-y-4 border-[#DDD9CF] bg-white shadow-sm">
              <div className="flex items-center justify-between pb-3 border-b border-[#DDD9CF]">
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-[#2F6F68]" />
                  <h3 className="text-sm font-bold text-[#29322F] uppercase">Station Passenger Volume Ranking</h3>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-[#F7F5EF] text-[#6F8F87] text-[10px] uppercase border-b border-[#DDD9CF]">
                    <tr>
                      <th className="py-2 px-2 font-semibold">Station Complex</th>
                      <th className="py-2 px-2 font-semibold">Avg Hourly</th>
                      <th className="py-2 px-2 font-semibold">Peak Hour</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#DDD9CF]">
                    {traffic?.top_stations.slice(0, 7).map((st) => (
                      <tr key={st.station_complex_id} className="hover:bg-[#F7F5EF]/50">
                        <td className="py-2 px-2 text-[#29322F] font-semibold">{st.station_complex}</td>
                        <td className="py-2 px-2 text-[#2F6F68] font-bold">{Math.round(st.avg_hourly_demand).toLocaleString()}</td>
                        <td className="py-2 px-2 text-[#C58A3A] font-bold">{Math.round(st.peak_demand).toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          </div>
        </div>
      )}

      {subTab === 'performance' && (
        <Card className="space-y-4 border-[#DDD9CF] bg-white shadow-sm">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 pb-3 border-b border-[#DDD9CF]">
            <div className="flex items-center gap-2">
              <Activity className="w-5 h-5 text-[#2F6F68]" />
              <h3 className="text-sm font-bold text-[#29322F] uppercase tracking-wide">
                Target Station Hub Performance Matrix (Observed vs Forecast)
              </h3>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#F7F5EF] text-[#6F8F87] text-[10px] uppercase border-b border-[#DDD9CF] font-semibold">
                <tr>
                  <th className="py-2.5 px-3">ID</th>
                  <th className="py-2.5 px-3">Station Complex</th>
                  <th className="py-2.5 px-3">Observed Entry Demand</th>
                  <th className="py-2.5 px-3">Forecast Next-Hour</th>
                  <th className="py-2.5 px-3">Crowd Risk Tier</th>
                  <th className="py-2.5 px-3">Risk Evidence</th>
                  <th className="py-2.5 px-3">Data Source</th>
                  <th className="py-2.5 px-3">Operator Advisory Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#DDD9CF]">
                {stations.map((st) => (
                  <tr key={st.station_complex_id} className="hover:bg-[#F7F5EF]/50">
                    <td className="py-2.5 px-3 text-[#6F8F87] font-sans">{st.station_complex_id}</td>
                    <td className="py-2.5 px-3 text-[#29322F] font-bold">{st.station_complex}</td>
                    <td className="py-2.5 px-3 text-[#6F8F87]">{Math.round(st.latest_passenger_count).toLocaleString()} pax</td>
                    <td className="py-2.5 px-3 text-[#2F6F68] font-bold">{Math.round(st.predicted_next_hour).toLocaleString()} pax</td>
                    <td className="py-2.5 px-3">
                      <Badge
                        variant={
                          st.crowd_risk === 'CRITICAL'
                            ? 'rose'
                            : st.crowd_risk === 'HIGH'
                            ? 'amber'
                            : st.crowd_risk === 'MODERATE'
                            ? 'amber'
                            : 'emerald'
                        }
                      >
                        {st.crowd_risk}
                      </Badge>
                    </td>
                    <td className="py-2.5 px-3 text-[#6F8F87] text-[10px]">{st.risk_explanation || 'Historical demand profiling'}</td>
                    <td className="py-2.5 px-3">
                      <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                        st.data_state?.includes('LIVE') ? 'bg-cyan-50 text-cyan-700 border border-cyan-200' : 'bg-[#F7F5EF] text-[#6F8F87] border border-[#DDD9CF]'
                      }`}>{st.data_state || 'HISTORICAL'}</span>
                    </td>
                    <td className="py-2.5 px-3 text-[#6F8F87] max-w-xs truncate">{st.recommended_action}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}


    </div>
  );
};
