import React, { useState, useEffect, useCallback } from 'react';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import StationModal from './components/StationModal';

// Pages
import Overview from './pages/Overview';
import CrowdMonitoring from './pages/CrowdMonitoring';
import TrainTracking from './pages/TrainTracking';
import ScheduleManagement from './pages/ScheduleManagement';
import AlertsCenter from './pages/AlertsCenter';
import RealTimePrediction from './pages/RealTimePrediction';
import DemandForecasting from './pages/DemandForecasting';
import ModelComparison from './pages/ModelComparison';
import DatasetAnalytics from './pages/DatasetAnalytics';

import { api } from './api/client';

const INITIAL_ALERTS = [
  {
    id: 'ALT-1001',
    timestamp: '08:15:30',
    station: 'Grand Central - 42 St',
    borough: 'Manhattan',
    severity: 'High',
    level: 'High',
    message: 'Overcrowding Surge Alert: Inflow exceeding normal morning peak baseline.',
    recommendation: 'Increase train frequency. Deploy standby trains on Lexington Line.',
    status: 'Active',
  },
  {
    id: 'ALT-1002',
    timestamp: '08:18:12',
    station: '149 St - Grand Concourse',
    borough: 'Bronx',
    severity: 'High',
    level: 'High',
    message: 'High platform density detected at key Bronx inter-corridor transfer vault.',
    recommendation: 'Increase train frequency to 2-minute headway.',
    status: 'Active',
  },
  {
    id: 'ALT-1003',
    timestamp: '08:22:45',
    station: 'Atlantic Av - Barclays Ctr',
    borough: 'Brooklyn',
    severity: 'Medium',
    level: 'Medium',
    message: 'Moderate crowd accumulation on Broadway corridor platform.',
    recommendation: 'Maintain standard schedule. Monitor platform passenger inflows.',
    status: 'Active',
  },
  {
    id: 'ALT-1004',
    timestamp: '08:24:00',
    station: 'Times Sq - 42 St',
    borough: 'Manhattan',
    severity: 'High',
    level: 'High',
    message: 'Multi-corridor passenger transfer surge between Lines 1, 7, and N.',
    recommendation: 'Deploy platform control staff and step dispatch to 30 trains/hr.',
    status: 'Acknowledged',
  },
  {
    id: 'ALT-1005',
    timestamp: '08:26:15',
    station: 'Woodlawn',
    borough: 'Bronx',
    severity: 'Low',
    level: 'Low',
    message: 'Normal Operations: Station running smoothly within capacity limits.',
    recommendation: 'Standard or reduced frequency is sufficient.',
    status: 'Resolved',
  },
];

export default function App() {
  const [activeModule, setActiveModule] = useState('overview');
  const [apiHealth, setApiHealth] = useState(null);
  const [stationsData, setStationsData] = useState(null);
  const [trainsData, setTrainsData] = useState(null);
  const [activeHour, setActiveHour] = useState(8);
  const [alerts, setAlerts] = useState(INITIAL_ALERTS);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [inspectedStation, setInspectedStation] = useState(null);
  const [scheduleTargetLevel, setScheduleTargetLevel] = useState('High');

  // Load backend telemetry on startup
  const fetchHealthAndBaseData = useCallback(async () => {
    try {
      const health = await api.getHealth();
      setApiHealth(health);
    } catch (e) {
      setApiHealth({ status: 'degraded', model_loaded: false, model_name: 'Random Forest' });
    }

    try {
      const [stRes, trRes] = await Promise.all([
        api.getStations({ hour: activeHour }),
        api.getTrains(3.0),
      ]);
      setStationsData(stRes);
      setTrainsData(trRes);
    } catch (e) {
      console.warn('Initial data loading warning:', e);
    }
  }, [activeHour]);

  useEffect(() => {
    fetchHealthAndBaseData();
  }, [fetchHealthAndBaseData]);

  // Handle Hour Change in Heatmap
  const handleHourChange = async (hour) => {
    setActiveHour(hour);
    try {
      const stRes = await api.getStations({ hour });
      setStationsData(stRes);
    } catch (e) {
      console.error('Failed to update stations for hour:', e);
    }
  };

  // Manual or step refresh
  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      const [trRes, stRes] = await Promise.all([
        api.getTrains(3.0),
        api.getStations({ hour: activeHour }),
      ]);
      setTrainsData(trRes);
      setStationsData(stRes);
    } catch (e) {
      console.error('Refresh error:', e);
    } finally {
      setIsRefreshing(false);
    }
  };

  // Train delay injector handler
  const handleInjectTrainDelay = async (trainId, minutes) => {
    return api.injectTrainDelay(trainId, minutes);
  };

  // Alert management
  const handleAcknowledgeAlert = (alertId) => {
    setAlerts((prev) =>
      prev.map((a) => (a.id === alertId ? { ...a, status: 'Acknowledged' } : a))
    );
  };

  const handleResolveAlert = (alertId) => {
    setAlerts((prev) =>
      prev.map((a) => (a.id === alertId ? { ...a, status: 'Resolved' } : a))
    );
  };

  const handleAddAlert = (newAlert) => {
    setAlerts((prev) => [newAlert, ...prev]);
  };

  // Navigate helper
  const handleNavigate = (moduleId, extraState = {}) => {
    setActiveModule(moduleId);
    if (extraState.scheduleLevel) {
      setScheduleTargetLevel(extraState.scheduleLevel);
    }
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Compute active module title
  const moduleTitles = {
    overview: 'Operations Console & KPI Overview',
    'crowd-monitoring': 'Subway Crowd Monitoring & Geospatial Heatmap',
    'train-tracking': 'Live Subway Train Tracking & Kinematics',
    'schedule-management': 'Operations Scheduling & Timetable Optimization',
    'alerts-center': 'Alerts, Incident Log & Emergency Dispatch',
    'real-time-prediction': 'Real-Time Crowd Congestion Inference',
    'demand-forecasting': 'Passenger Demand Multi-Horizon Forecasting',
    'model-comparison': 'Model Comparison & Benchmarking Leaderboard',
    'dataset-analytics': 'Dataset Analytics & Exploratory Data Analysis (EDA)',
  };

  const activeAlertsCount = alerts.filter(
    (a) => (a.severity === 'High' || a.level === 'High') && a.status !== 'Resolved'
  ).length;

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#0B1220] text-slate-100">
      {/* Navigation Sidebar */}
      <Sidebar
        activeModule={activeModule}
        onSelectModule={(id) => handleNavigate(id)}
        alertCount={activeAlertsCount}
      />

      {/* Main Operations Frame */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        {/* Fixed Header */}
        <Header
          apiHealth={apiHealth}
          onRefresh={handleRefresh}
          isRefreshing={isRefreshing}
          activeModuleTitle={moduleTitles[activeModule]}
        />

        {/* Scrollable Work Area */}
        <main className="flex-1 overflow-y-auto p-6 space-y-6">
          {activeModule === 'overview' && (
            <Overview
              stationsData={stationsData}
              trainsData={trainsData}
              alerts={alerts}
              onNavigate={handleNavigate}
              onInspectStation={(st) => setInspectedStation(st)}
            />
          )}

          {activeModule === 'crowd-monitoring' && (
            <CrowdMonitoring
              stationsData={stationsData}
              onInspectStation={(st) => setInspectedStation(st)}
              onHourChange={handleHourChange}
              activeHour={activeHour}
            />
          )}

          {activeModule === 'train-tracking' && (
            <TrainTracking
              trainsData={trainsData}
              onRefresh={handleRefresh}
              isRefreshing={isRefreshing}
              onInjectDelay={handleInjectTrainDelay}
            />
          )}

          {activeModule === 'schedule-management' && (
            <ScheduleManagement initialLevel={scheduleTargetLevel} />
          )}

          {activeModule === 'alerts-center' && (
            <AlertsCenter
              alerts={alerts}
              onAcknowledgeAlert={handleAcknowledgeAlert}
              onResolveAlert={handleResolveAlert}
              onAddAlert={handleAddAlert}
            />
          )}

          {activeModule === 'real-time-prediction' && (
            <RealTimePrediction
              stations={stationsData?.stations || []}
              onDispatchAlert={handleAddAlert}
              onNavigate={handleNavigate}
            />
          )}

          {activeModule === 'demand-forecasting' && (
            <DemandForecasting
              onDispatchAlert={handleAddAlert}
              onNavigate={handleNavigate}
            />
          )}

          {activeModule === 'model-comparison' && <ModelComparison />}

          {activeModule === 'dataset-analytics' && <DatasetAnalytics />}
        </main>
      </div>

      {/* Station Details Inspection Modal */}
      {inspectedStation && (
        <StationModal
          station={inspectedStation}
          onClose={() => setInspectedStation(null)}
          onDispatchAlert={(st) => {
            handleAddAlert({
              id: `ALT-${Date.now().toString().slice(-4)}`,
              station: st.name,
              borough: st.borough,
              severity: st.congestion_level,
              level: st.congestion_level,
              message: st.alert_message || `Congestion surge at ${st.name}.`,
              recommendation: st.recommendation,
              timestamp: new Date().toLocaleTimeString(),
              status: 'Active',
            });
            handleNavigate('alerts-center');
          }}
          onSelectSchedule={(level) => {
            handleNavigate('schedule-management', { scheduleLevel: level });
          }}
        />
      )}
    </div>
  );
}
