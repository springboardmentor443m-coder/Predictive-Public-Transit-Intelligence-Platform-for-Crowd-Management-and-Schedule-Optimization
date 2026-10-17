import React, { useState, useEffect, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import { mlService, MLSummary, MLStationStatus, DelayImpactRecord, NetworkRiskRecord, SchedulingIntelligenceRecord, NetworkSummary } from '../services/mlService';
import { alertService, OperationalAlert, AlertSummary } from '../services/alertService';
import { liveService, NormalizedServiceAlert } from '../services/liveService';
import { TrafficAnalyticsResponse, RiskDistribution, FeatureImportance } from '../services/mlService';
import { cachedFetch } from '../services/cache';
import { NetworkTopologyVisualizer } from '../components/live/NetworkTopologyVisualizer';
import { StationIntelligencePanel } from '../components/live/StationIntelligencePanel';
import { DelayImpactVisualizer } from '../components/live/DelayImpactVisualizer';
import { SchedulingIntelligenceVisualizer } from '../components/live/SchedulingIntelligenceVisualizer';
import { AnalyticsMatrixVisualizer } from '../components/live/AnalyticsMatrixVisualizer';
import { AlertCenterVisualizer } from '../components/live/AlertCenterVisualizer';
import { RealtimeCrowdPanel } from '../components/live/RealtimeCrowdPanel';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { TrendingUp, AlertTriangle, RefreshCw, Info } from 'lucide-react';

export const MLDashboardPage: React.FC = () => {
  const location = useLocation();
  const path = location.pathname;
  
  let currentView = 'crowd';
  if (path === '/network') currentView = 'network';
  if (path === '/alerts') currentView = 'alerts';
  if (path === '/analytics' || path === '/diagnostics' || path === '/history') currentView = 'analytics';

  const [stations, setStations] = useState<MLStationStatus[]>([]);
  const [summary, setSummary] = useState<MLSummary | null>(null);
  const [networkSummary, setNetworkSummary] = useState<NetworkSummary | null>(null);
  const [delays, setDelays] = useState<DelayImpactRecord[]>([]);
  const [networkRisks, setNetworkRisks] = useState<NetworkRiskRecord[]>([]);
  const [schedules, setSchedules] = useState<SchedulingIntelligenceRecord[]>([]);
  
  const [activeAlerts, setActiveAlerts] = useState<OperationalAlert[]>([]);
  const [alertHistory, setAlertHistory] = useState<OperationalAlert[]>([]);
  const [alertSummary, setAlertSummary] = useState<AlertSummary | null>(null);
  const [liveAlerts, setLiveAlerts] = useState<NormalizedServiceAlert[]>([]);
  
  const [trafficAnalytics, setTrafficAnalytics] = useState<TrafficAnalyticsResponse | null>(null);
  const [riskDist, setRiskDist] = useState<RiskDistribution[]>([]);
  const [featureImportances, setFeatureImportances] = useState<FeatureImportance[]>([]);

  const [selectedStationId, setSelectedStationId] = useState<string>('164');
  const [selectedStationName, setSelectedStationName] = useState<string>('Times Sq-42 St');
  const [stationDetail, setStationDetail] = useState<any>(null);
  const [connectionsDetail, setConnectionsDetail] = useState<any>(null);

  const [loading, setLoading] = useState<boolean>(true);
  const [detailLoading, setDetailLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboardData = async (force = false) => {
    setLoading(true);
    setError(null);
    // When forced (manual refresh), bypass cache for live endpoints
    const alertTTL = force ? 0 : 15_000;
    const mlTTL = force ? 0 : 30_000;
    const slowTTL = force ? 0 : 60_000;
    try {
      const [
        stData, sumData, netSum, delData, netRiskData, schedData,
        actAlerts, histAlerts, altSum, liveAl, trafData, riskDistData, featImportData
      ] = await Promise.all([
        cachedFetch('ml:stations',     () => mlService.getStations().catch(() => []),               mlTTL),
        cachedFetch('ml:summary',      () => mlService.getSummary().catch(() => null),              mlTTL),
        cachedFetch('ml:netSummary',   () => mlService.getNetworkSummary().catch(() => null),       slowTTL),
        cachedFetch('ml:delayImpact',  () => mlService.getDelayImpact().catch(() => []),            mlTTL),
        cachedFetch('ml:networkRisk',  () => mlService.getNetworkRisk().catch(() => []),            mlTTL),
        cachedFetch('ml:schedules',    () => mlService.getSchedulingIntelligence().catch(() => []), mlTTL),
        cachedFetch('ml:actAlerts',    () => alertService.getActiveAlerts().catch(() => []),        alertTTL),
        cachedFetch('ml:histAlerts',   () => alertService.getAlertHistory().catch(() => []),        alertTTL),
        cachedFetch('ml:alertSummary', () => alertService.getAlertSummary().catch(() => null),      alertTTL),
        cachedFetch('ml:liveAlerts',   () => liveService.getAlerts().catch(() => []),               mlTTL),
        cachedFetch('ml:traffic',      () => mlService.getTrafficAnalytics().catch(() => null),     slowTTL),
        cachedFetch('ml:riskDist',     () => mlService.getRiskDistribution().catch(() => []),       mlTTL),
        cachedFetch('ml:featImport',   () => mlService.getFeatureImportance().catch(() => []),      slowTTL),
      ]);

      setStations(stData);
      setSummary(sumData);
      setNetworkSummary(netSum);
      setDelays(delData);
      setNetworkRisks(netRiskData);
      setSchedules(schedData);
      setActiveAlerts(actAlerts);
      setAlertHistory(histAlerts);
      setAlertSummary(altSum);
      setLiveAlerts(liveAl);
      setTrafficAnalytics(trafData);
      setRiskDist(riskDistData);
      setFeatureImportances(featImportData);

    } catch (err: any) {
      console.error('Error fetching operations dashboard data:', err);
      setError('Failed to connect to MetroFlow Operations API.');
    } finally {
      setLoading(false);
    }
  };

  const fetchStationIntelligence = async (stName: string) => {
    setDetailLoading(true);
    try {
      const [detail, conn] = await Promise.all([
        mlService.getStationDetail(stName).catch(() => null),
        mlService.getStationConnections(stName).catch(() => null)
      ]);
      setStationDetail(detail);
      setConnectionsDetail(conn);
    } catch (err) {
      console.error('Failed to fetch intelligence for station', err);
    } finally {
      setDetailLoading(false);
    }
  };

  // Auto-refresh every 30s for live data
  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(() => fetchDashboardData(), 30_000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (selectedStationName) {
      fetchStationIntelligence(selectedStationName);
    }
  }, [selectedStationName]);

  const handleSelectStation = (stId: string, stName: string) => {
    setSelectedStationId(stId);
    setSelectedStationName(stName);
  };

  const selectedRiskRecord = networkRisks.find(r => r.station_complex_id === selectedStationId || r.station_complex.includes(selectedStationName)) || null;

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 glass-panel p-6 rounded-2xl border border-[#DDD9CF] bg-white shadow-sm">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-[#29322F] font-sans tracking-wide flex items-center gap-2 capitalize">
              {currentView.replace('-', ' ')}
            </h1>
            <Badge variant={summary?.data_state?.includes('LIVE') ? 'cyan' : 'slate'}>
              {summary?.data_state?.includes('LIVE') ? 'LIVE ML ENGINE' : 'CONNECTING'}
            </Badge>
          </div>
          <p className="text-sm text-[#6F8F87] mt-1 font-sans">
            Real-time predictions · Random Forest · GTFS-RT telemetry
          </p>
        </div>

        <div className="flex items-center gap-3 font-sans">
          <Button variant="secondary" size="sm" onClick={() => fetchDashboardData(true)} isLoading={loading}>
            <RefreshCw className="w-3.5 h-3.5 mr-1" />
            Refresh
          </Button>
        </div>
      </div>

      {error && (
        <Card className="border-[#B9574B] bg-[#B9574B]/10 text-[#B9574B] font-sans text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-[#B9574B]" />
          <span>{error}</span>
        </Card>
      )}

      {currentView === 'crowd' && (
        <div className="space-y-6">
          {/* NEW — Real-time RandomForest crowd predictions */}
          <RealtimeCrowdPanel />

          {/* Existing station intelligence panel */}
          <StationIntelligencePanel
            stationRisk={selectedRiskRecord}
            connections={connectionsDetail}
            delays={delays}
          />
        </div>
      )}

      {currentView === 'network' && (
        <div className="space-y-6">
          <NetworkTopologyVisualizer
            networkRisks={networkRisks}
            selectedStationId={selectedStationId}
            onSelectStation={handleSelectStation}
            connectionsDetail={connectionsDetail}
          />
        </div>
      )}
      
      {currentView === 'advisories' && (
        <div className="space-y-6">
          <DelayImpactVisualizer delays={delays} />
          <SchedulingIntelligenceVisualizer records={schedules} />
        </div>
      )}

      {currentView === 'alerts' && (
        <AlertCenterVisualizer
          alerts={activeAlerts}
          history={alertHistory}
          summary={alertSummary}
          onRefresh={fetchDashboardData}
        />
      )}

      {currentView === 'analytics' && (
        <AnalyticsMatrixVisualizer
          traffic={trafficAnalytics}
          riskDist={riskDist}
          featureImportances={featureImportances}
          summary={summary}
          stations={stations}
        />
      )}
    </div>
  );
};
