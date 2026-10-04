import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import ErrorBoundary from './components/ErrorBoundary';
import LiveOpsDashboard from './components/LiveOpsDashboard';
import DelaySimulator from './components/DelaySimulator';
import MLInsights from './components/MLInsights';
import PredictionCalculator from './components/PredictionCalculator';
import ScheduleAdvisoryTable from './components/ScheduleAdvisoryTable';
import NetworkAnalytics from './components/NetworkAnalytics';
import { checkBackendHealth, fetchMetadata } from './services/api';
import { 
  Train, 
  Activity, 
  Layers, 
  Zap, 
  Cpu, 
  ExternalLink,
  ShieldCheck,
  AlertCircle
} from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('ml');
  const [backendStatus, setBackendStatus] = useState(null);
  const [metadata, setMetadata] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(new Date().toLocaleTimeString());

  useEffect(() => {
    const initApp = async () => {
      const health = await checkBackendHealth();
      setBackendStatus(health);

      const meta = await fetchMetadata();
      if (meta) setMetadata(meta);

      setLastUpdated(new Date().toLocaleTimeString());
    };

    initApp();
    const interval = setInterval(initApp, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-[#080d1a] text-slate-100 flex flex-col font-sans relative selection:bg-cyan-500 selection:text-white">
      
      {/* Background ambient lighting */}
      <div className="ambient-glow"></div>

      {/* Navigation & Header */}
      <Header 
        activeTab={activeTab} 
        setActiveTab={setActiveTab} 
        backendStatus={backendStatus}
        lastUpdated={lastUpdated}
      />

      {/* Main Content Area with Generous Spacing and Breathing Room */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-10 relative z-10 space-y-10">
        
        {/* Connection Notice if Backend is Offline */}
        {backendStatus?.status === 'Offline' && (
          <div className="mb-6 p-4 rounded-2xl bg-amber-950/40 border border-amber-500/40 text-amber-300 text-xs font-mono flex items-center justify-between shadow-lg">
            <div className="flex items-center space-x-2.5">
              <AlertCircle className="w-5 h-5 text-amber-400 flex-shrink-0" />
              <span>
                Backend offline or starting up on <code className="text-amber-200">http://localhost:8000</code>. Local predictive intelligence is active.
              </span>
            </div>
            <span className="hidden sm:inline-block px-2.5 py-1 rounded-md bg-amber-500/20 text-amber-300 border border-amber-500/30">
              Standby Mode
            </span>
          </div>
        )}

        {/* Dynamic Tab Rendering — every tab is wrapped so one broken view
            cannot unmount the whole app and leave a blank page. */}
        {activeTab === 'live' && (
          <section aria-label="Live Crowd Operations">
            <ErrorBoundary key="live">
              <LiveOpsDashboard />
            </ErrorBoundary>
          </section>
        )}

        {activeTab === 'schedule' && (
          <section aria-label="Train Schedule & Delay Propagation">
            <ErrorBoundary key="schedule">
              <DelaySimulator />
            </ErrorBoundary>
          </section>
        )}

        {activeTab === 'ml' && (
          <section aria-label="ML Model Evaluation">
            <ErrorBoundary key="ml">
              <MLInsights />
            </ErrorBoundary>
          </section>
        )}

        {activeTab === 'prediction' && (
          <section aria-label="Live Crowd Prediction">
            <ErrorBoundary key="prediction">
              <PredictionCalculator />
            </ErrorBoundary>
          </section>
        )}

        {activeTab === 'advisory' && (
          <section aria-label="Fleet Schedule Advisory">
            <ErrorBoundary key="advisory">
              <ScheduleAdvisoryTable />
            </ErrorBoundary>
          </section>
        )}

        {activeTab === 'analytics' && (
          <section aria-label="Network Analytics & Model Evaluation">
            <ErrorBoundary key="analytics">
              <NetworkAnalytics />
            </ErrorBoundary>
          </section>
        )}

      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-[#090d16]/90 mt-12 py-6 relative z-10 text-xs text-slate-500 font-mono">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 rounded-full bg-cyan-400"></div>
            <span className="text-slate-400 font-semibold">MetroFlow AI Transit Platform</span>
            <span>•</span>
            <span>FastAPI + XGBoost Regressor + React Vite</span>
          </div>

          <div className="flex items-center space-x-4">
            <span className="text-slate-400">
              Dataset: <span className="text-cyan-400">AI_MetroFlow_Master_Dataset.xlsx</span>
            </span>
            <span>•</span>
            <span className="text-slate-400">
              5 stations · 4 lines
            </span>
            <span>•</span>
            <span className="text-emerald-400 flex items-center gap-1">
              <ShieldCheck className="w-3.5 h-3.5" />
              CORS Enabled
            </span>
          </div>

        </div>
      </footer>

    </div>
  );
}
