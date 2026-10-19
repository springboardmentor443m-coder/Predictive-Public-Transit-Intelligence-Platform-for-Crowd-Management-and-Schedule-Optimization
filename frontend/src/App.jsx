import {
  BrowserRouter,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";

import "./App.css";

import AppLayout from "./components/AppLayout";
import { isAuthenticated } from "./services/api";

import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import DemandPulse from "./pages/DemandPulse";
import CrowdMonitoring from "./pages/CrowdMonitoring";
import AIPredictions from "./pages/AIPredictions";
import Schedules from "./pages/Schedules";
import Analytics from "./pages/Analytics";

function ProtectedRoute({ children }) {
  return isAuthenticated() ? (
    children
  ) : (
    <Navigate to="/login" replace />
  );
}

function LayoutPage({ children }) {
  return (
    <ProtectedRoute>
      <AppLayout>{children}</AppLayout>
    </ProtectedRoute>
  );
}

function PlaceholderPage({ title, description }) {
  return (
    <main className="placeholder-page">
      <h1>{title}</h1>
      <p>{description}</p>
    </main>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />

        <Route
          path="/"
          element={
            <LayoutPage>
              <Dashboard />
            </LayoutPage>
          }
        />

        <Route
          path="/monitoring"
          element={
            <LayoutPage>
              <DemandPulse />
            </LayoutPage>
          }
        />

        <Route
          path="/crowd-monitoring"
          element={
            <LayoutPage>
              <CrowdMonitoring />
            </LayoutPage>
          }
        />

        <Route
          path="/predictions"
          element={
            <LayoutPage>
              <AIPredictions />
            </LayoutPage>
          }
        />

        <Route
          path="/scheduling"
          element={
            <LayoutPage>
              <Schedules />
            </LayoutPage>
          }
        />

        <Route
          path="/operators"
          element={
            <LayoutPage>
              <PlaceholderPage
                title="Operators"
                description="Operational information and service management."
              />
            </LayoutPage>
          }
        />

        <Route
          path="/alerts"
          element={
            <LayoutPage>
              <PlaceholderPage
                title="Alerts"
                description="Risk levels, generated alerts and operational warnings."
              />
            </LayoutPage>
          }
        />

        
        <Route
          path="/analytics"
          element={
            <LayoutPage>
              <Analytics />
            </LayoutPage>
          }
        />


        <Route
          path="/settings"
          element={
            <LayoutPage>
              <PlaceholderPage
                title="Settings"
                description="Application settings."
              />
            </LayoutPage>
          }
        />

        <Route
          path="/station-intelligence"
          element={
            <Navigate to="/crowd-monitoring" replace />
          }
        />

        <Route
          path="/train-operations"
          element={
            <Navigate to="/monitoring" replace />
          }
        />

        <Route
          path="/risk"
          element={<Navigate to="/alerts" replace />}
        />

        <Route
          path="/data-models"
          element={<Navigate to="/analytics" replace />}
        />

        <Route
          path="*"
          element={<Navigate to="/" replace />}
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;