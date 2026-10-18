import React, { useEffect, useState, useRef } from 'react';
import { Navbar } from './components/Navbar';
import { CrowdMonitorView } from './components/CrowdMonitorView';
import { PredictionsView } from './components/PredictionsView';
import { SchedulingView } from './components/SchedulingView';
import { AlertsView } from './components/AlertsView';
import { AnalyticsView } from './components/AnalyticsView';
import { StaffView } from './components/StaffView';
import { StationModal } from './components/StationModal';
import { LoginModal } from './components/LoginModal';
import { api } from './services/api';
import { User, NetworkSnapshot, HorizonPrediction } from './types';

export default function App() {
  const [currentUser, setCurrentUser] = useState<User | null>(() => {
    const saved = api.getCurrentUser();
    // Default to pre-seeded Admin account for instant pairs-testing
    return saved || {
      id: 1,
      email: 'admin@metroflow.ny',
      name: 'Sarah Chen',
      role: 'admin',
      title: 'Chief Transit Director',
      badge_id: 'NY-ADM-01'
    };
  });

  const [activeTab, setActiveTab] = useState<string>('monitor');
  const [activeHorizon, setActiveHorizon] = useState<number>(0); // 0 = Live Now, 15 = +15m, 30 = +30m, 60 = +1h
  const [snapshot, setSnapshot] = useState<NetworkSnapshot | null>(null);
  const [predictedStations, setPredictedStations] = useState<HorizonPrediction[] | null>(null);
  const [selectedStationId, setSelectedStationId] = useState<string | null>(null);
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);
  const [wsConnected, setWsConnected] = useState(false);
  const [unreadAlertCount, setUnreadAlertCount] = useState(3);

  const wsRef = useRef<WebSocket | null>(null);

  // Fetch initial REST snapshot & alert counts
  useEffect(() => {
    api.getLiveSnapshot()
      .then(data => setSnapshot(data))
      .catch(err => console.error('Snapshot error:', err));

    api.getAlerts()
      .then(data => setUnreadAlertCount(data.active_count))
      .catch(err => console.error('Alerts error:', err));
  }, []);

  // WebSocket Live Telemetry Feed with automatic reconnect
  useEffect(() => {
    let reconnectTimeout: any;

    const connectWebSocket = () => {
      try {
        const ws = new WebSocket('ws://localhost:8000/ws/live');
        wsRef.current = ws;

        ws.onopen = () => {
          setWsConnected(true);
        };

        ws.onmessage = (event) => {
          try {
            const data: NetworkSnapshot = JSON.parse(event.data);
            setSnapshot(data);
          } catch (e) {
            console.error('Failed to parse WS snapshot', e);
          }
        };

        ws.onclose = () => {
          setWsConnected(false);
          reconnectTimeout = setTimeout(connectWebSocket, 3000);
        };

        ws.onerror = () => {
          setWsConnected(false);
        };
      } catch (err) {
        console.error('WS init error', err);
        reconnectTimeout = setTimeout(connectWebSocket, 3000);
      }
    };

    connectWebSocket();

    // Fallback polling every 3 seconds to ensure guaranteed live ticking
    const pollingInterval = setInterval(() => {
      if (!wsConnected) {
        api.getLiveSnapshot()
          .then(data => setSnapshot(data))
          .catch(() => {});
      }
    }, 3000);

    return () => {
      if (wsRef.current) wsRef.current.close();
      clearTimeout(reconnectTimeout);
      clearInterval(pollingInterval);
    };
  }, [wsConnected]);

  // When activeHorizon changes, fetch predicted station weights if future horizon
  useEffect(() => {
    if (activeHorizon === 0) {
      setPredictedStations(null);
    } else {
      api.getNetworkHorizonPredictions(activeHorizon)
        .then(res => setPredictedStations(res.stations))
        .catch(err => console.error('Failed to fetch horizon predictions', err));
    }
  }, [activeHorizon]);

  const handleLogout = () => {
    api.logout();
    setCurrentUser(null);
    setIsLoginModalOpen(true);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Top Navbar */}
      <Navbar
        currentUser={currentUser}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        activeHorizon={activeHorizon}
        setActiveHorizon={setActiveHorizon}
        wsConnected={wsConnected}
        onOpenLogin={() => setIsLoginModalOpen(true)}
        onLogout={handleLogout}
        unreadAlertCount={unreadAlertCount}
      />

      {/* Main Operational Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8">
        {activeTab === 'monitor' && (
          <CrowdMonitorView
            snapshot={snapshot}
            predictedStations={predictedStations}
            activeHorizon={activeHorizon}
            onSelectStation={(id) => setSelectedStationId(id)}
            onOpenAlerts={() => setActiveTab('alerts')}
          />
        )}

        {activeTab === 'predictions' && (
          <PredictionsView
            onSelectStation={(id) => setSelectedStationId(id)}
            activeHorizon={activeHorizon}
            setActiveHorizon={setActiveHorizon}
          />
        )}

        {activeTab === 'scheduling' && (
          <SchedulingView currentUser={currentUser} />
        )}

        {activeTab === 'alerts' && (
          <AlertsView currentUser={currentUser} />
        )}

        {activeTab === 'analytics' && (
          <AnalyticsView />
        )}

        {activeTab === 'staff' && (
          <StaffView currentUser={currentUser} />
        )}
      </main>

      {/* Footer Branding */}
      <footer className="border-t border-slate-900 bg-slate-950/80 py-4 px-6 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>MetroFlow &bull; Enterprise Transit Operations & AI Crowd Scheduling Platform</span>
          <span className="font-mono text-[11px] text-slate-400">Station Feeds & Telemetry: Live New York Transit Network</span>
        </div>
      </footer>

      {/* Station In-Depth Drilldown Modal */}
      <StationModal
        stationId={selectedStationId}
        onClose={() => setSelectedStationId(null)}
      />

      {/* Login Authentication Modal */}
      <LoginModal
        isOpen={isLoginModalOpen}
        onClose={() => setIsLoginModalOpen(false)}
        onLoginSuccess={(user) => {
          setCurrentUser(user);
          setIsLoginModalOpen(false);
        }}
      />
    </div>
  );
}
