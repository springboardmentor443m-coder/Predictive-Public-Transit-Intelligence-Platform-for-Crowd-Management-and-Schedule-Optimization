import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar';
import { LiveMapPage } from './pages/LiveMapPage';
import { StationDetailPage } from './pages/StationDetailPage';
import { SchedulePage } from './pages/SchedulePage';
import { AlertsPage } from './pages/AlertsPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { LoginPage } from './pages/LoginPage';

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <BrowserRouter>
        <div className="min-h-screen bg-bg-main flex flex-col font-sans">
          <Navbar />
          <div className="flex flex-1">
            <Sidebar />
            <main className="flex-1 bg-bg-main overflow-y-auto">
              <Routes>
                <Route path="/" element={<LiveMapPage />} />
                <Route path="/stations/:stationCode" element={<StationDetailPage />} />
                <Route path="/schedule" element={<SchedulePage />} />
                <Route path="/alerts" element={<AlertsPage />} />
                <Route path="/analytics" element={<AnalyticsPage />} />
                <Route path="/login" element={<LoginPage />} />
              </Routes>
            </main>
          </div>
        </div>
      </BrowserRouter>
    </AuthProvider>
  );
};
