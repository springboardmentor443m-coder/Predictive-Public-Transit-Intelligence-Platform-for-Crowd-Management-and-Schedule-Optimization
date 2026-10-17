import { NavLink, useNavigate } from "react-router-dom";
import {
  Activity,
  BarChart3,
  CalendarClock,
  Gauge,
  LogOut,
  Settings,
  Users,
  TrainFront,
  BrainCircuit,
} from "lucide-react";

import { logoutUser } from "../services/api";
import "../styles/AppLayout.css";

function AppLayout({ children }) {
  const navigate = useNavigate();

  const handleLogout = () => {
    logoutUser();
    navigate("/login");
  };

  const navClass = ({ isActive }) =>
    `layout-nav-link ${isActive ? "active" : ""}`;

  return (
    <div className="app-shell">
      <aside className="app-sidebar">
        <div className="sidebar-brand">
          <div className="brand-mark">
            <TrainFront size={22} />
          </div>

          <div>
            <div className="brand-name">AI METROFLOW</div>
            <div className="brand-subtitle">
              TRANSIT INTELLIGENCE
            </div>
          </div>
        </div>

        <nav className="sidebar-navigation">
          <div className="nav-section">
            <div className="nav-section-title">OVERVIEW</div>

            <NavLink to="/" end className={navClass}>
              <Gauge size={18} />
              <span>Dashboard</span>
            </NavLink>
          </div>

          <div className="nav-section">
            <div className="nav-section-title">OPERATIONS</div>

            <NavLink to="/monitoring" className={navClass}>
              <Activity size={18} />
              <span>Network Monitoring</span>
            </NavLink>

            <NavLink to="/crowd-monitoring" className={navClass}>
              <Users size={18} />
              <span>Crowd Monitoring</span>
            </NavLink>

            <NavLink to="/scheduling" className={navClass}>
              <CalendarClock size={18} />
              <span>Scheduling</span>
            </NavLink>
          </div>

          <div className="nav-section">
            <div className="nav-section-title">INSIGHTS</div>

            <NavLink to="/predictions" className={navClass}>
              <BrainCircuit size={18} />
              <span>AI Predictions</span>
            </NavLink>

            <NavLink to="/analytics" className={navClass}>
              <BarChart3 size={18} />
              <span>Live Monitoring and Analytics</span>
            </NavLink>
          </div>
        </nav>

        <div className="sidebar-bottom">
          <NavLink to="/settings" className={navClass}>
            <Settings size={18} />
            <span>Settings</span>
          </NavLink>

          <button
            className="sidebar-bottom-link logout-button"
            type="button"
            onClick={handleLogout}
          >
            <LogOut size={18} />
            <span>Logout</span>
          </button>
        </div>
      </aside>

      <main className="app-main">{children}</main>
    </div>
  );
}

export default AppLayout;