import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from './contexts/ThemeContext';
import { AuthProvider } from './contexts/AuthContext';
import { ProtectedRoute } from './routes/ProtectedRoute';
import { RoleRoute } from './routes/RoleRoute';
import { DashboardLayout } from './components/layout/DashboardLayout';

import { LoginPage } from './pages/LoginPage';
import { MLDashboardPage } from './pages/MLDashboardPage';
import { DashboardOverviewPage } from './pages/DashboardOverviewPage';
import { LiveMonitoringPage } from './pages/LiveMonitoringPage';
import { ProfilePage } from './pages/ProfilePage';
import { UserManagementPage } from './pages/UserManagementPage';
import { AuditLogsPage } from './pages/AuditLogsPage';
import { NotFoundPage } from './pages/NotFoundPage';

export const App: React.FC = () => {
  return (
    <ThemeProvider>
      <AuthProvider>
        <Router>
        <Routes>
          {/* Public Routes */}
          <Route path="/login" element={<LoginPage />} />

          {/* Protected Operations Dashboard Routes */}
          <Route element={<ProtectedRoute />}>
            <Route element={<DashboardLayout />}>
              <Route path="/" element={<Navigate to="/overview" replace />} />
              <Route path="/overview" element={<DashboardOverviewPage />} />
              <Route path="/live-monitoring" element={<LiveMonitoringPage />} />
              
              {/* All these route to MLDashboardPage which handles them dynamically */}
              <Route path="/dashboard" element={<MLDashboardPage />} />
              <Route path="/ml-dashboard" element={<Navigate to="/dashboard" replace />} />
              <Route path="/network" element={<MLDashboardPage />} />
              <Route path="/alerts" element={<MLDashboardPage />} />
              <Route path="/analytics" element={<MLDashboardPage />} />
              <Route path="/history" element={<MLDashboardPage />} />
              <Route path="/diagnostics" element={<MLDashboardPage />} />
              
              <Route path="/profile" element={<ProfilePage />} />

              {/* Admin Only Routes */}
              <Route element={<RoleRoute allowedRoles={['ADMIN']} />}>
                <Route path="/admin/users" element={<UserManagementPage />} />
                <Route path="/admin/audit-logs" element={<AuditLogsPage />} />
              </Route>

              {/* Catch-all 404 Route */}
              <Route path="*" element={<NotFoundPage />} />
            </Route>
          </Route>
        </Routes>
      </Router>
    </AuthProvider>
    </ThemeProvider>
  );
};

export default App;
