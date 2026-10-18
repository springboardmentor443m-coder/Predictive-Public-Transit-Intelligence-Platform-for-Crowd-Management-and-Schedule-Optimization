# MetroFlow: AI Platform for Metro Crowd Management and Scheduling

MetroFlow is an enterprise-grade AI-powered metro crowd management, passenger flow forecasting, and automated train scheduling platform built with **Python (FastAPI)** and **React (Vite + Tailwind CSS + Leaflet)**.

---

## 📍 Exact Codebase Location on Your PC
```
C:\Users\91628\.gemini\antigravity\scratch\metroflow
```

---

## 🚀 Quick Start Execution

### Option 1: One-Click Master Launcher (Windows)
Double-click or run from terminal:
```cmd
C:\Users\91628\.gemini\antigravity\scratch\metroflow\start_metroflow.bat
```
*(Or in PowerShell: `.\start_metroflow.ps1`)*

This starts both the FastAPI backend and React frontend concurrently in two separate terminal windows.

---

### Option 2: Run Backend and Frontend Manually

#### Step 1: Start Backend Server
Open a terminal in the backend directory:
```bash
cd C:\Users\91628\.gemini\antigravity\scratch\metroflow\backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
- **Backend API**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Live Telemetry WebSocket**: `ws://127.0.0.1:8000/ws/live`

#### Step 2: Start Frontend Application
Open a second terminal in the frontend directory:
```bash
cd C:\Users\91628\.gemini\antigravity\scratch\metroflow\frontend
npm run dev
```
- **Web Application UI**: [http://localhost:5173](http://localhost:5173)

---

## 🔑 Pre-Seeded Role Credentials

The application includes two pre-configured roles with one-click quick switchers inside the login modal:

| Role | Email | Password | Access Privileges |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin@metroflow.ny` | `admin123` | Full system control, line headway scheduling, automated peak optimization, emergency broadcast dispatch, operator user management |
| **Operator** | `operator@metroflow.ny` | `operator123` | Real-time telemetry monitoring, line delay incident reporting, alert acknowledgment, manual headway tuning |

---

## 🧩 Modules Implemented

### 1. User Management Module
- **Role-Based Access Control (RBAC)**: Distinct permissions for `admin` and `operator`.
- **Operator Directory**: Live view of active controllers with badge IDs and titles.
- **Operator Account Provisioning**: Admins can provision new operator accounts with encrypted passcodes.

### 2. Crowd Monitoring Module
- **Live Network Overview KPIs**: Total active network passengers, network density %, bottleneck hubs, active train fleet, live turnstile inflow and outflow rates.
- **CartoDB Dark Interactive Map**: Leaflet map centered on New York City transit lines (Lines 1, 2, 3, 4, 5, 6, 7, A, C, E, L, N, Q, R) with official route colors.
- **Real-Time Moving Trains**: Real-time GPS train markers moving along track routes with speed, occupancy, and status.
- **Station Drilldown Modal**: Deep analytics for every station showing live turnstile entry/exit rates, 12-minute sensor trend, platform capacity gauge, and predictive horizons.

### 3. AI Prediction Module (Multi-Horizon Demand Forecasting)
- **Predictive Horizons**: Toggle between **Live Now**, **+15 Minutes**, **+30 Minutes**, **+1 Hour**, and **+2 Hours**.
- **Interactive Heatmap Transformation**: The subway map markers immediately shift colors to show the predicted crowd density at that future time.
- **Multi-Station Horizon Progression Curves**: Visual curves showing projected passenger load progression over +15m, +30m, +1h, and +2h.
- **Actionable Dispatch Directives**: Real-time headway tightening recommendations and bypass shuttle suggestions.

### 4. Scheduling & Headway Optimization Module
- **Headway Matrix**: Live table of all subway lines with current headway, AI-recommended headway, and peak status.
- **Frequency Adjuster**: Interactive headway slider (2.0 min to 10.0 min) with operational justification logging.
- **Automated Peak Headway Optimization**: Single-click algorithmic optimization that tightens frequency on high-density corridors.
- **Incident & Delay Simulator**: Form to report train delays (1-45 min) with immediate network alert propagation.

### 5. Alert & Emergency Notification Module
- **Real-Time Alert Feed**: Filter by Overcrowding, Delays, Emergency, and Maintenance.
- **Emergency Passenger Broadcast Dispatcher**: High-priority broadcast console that transmits immediate announcements across station displays.
- **Alert Resolution**: Dispatchers can acknowledge and resolve warnings with audit logging.

### 6. Analytics Dashboard Module
- **24-Hour Commuter Demand Profile vs Offered Capacity**: Complete ridership curve with Morning (7:30-9:30 AM) and Evening (4:30-7:00 PM) peak surges.
- **Turnstile Throughput Comparison**: Inflow vs outflow bar charts across top interchange hubs.
- **Station Congestion Rankings**: Ranked list of all primary stations by ridership density.
- **Operational Audit Trail**: Timestamped log of headway adjustments, peak optimizations, and incident reports.

---

## 🛠️ Technology Stack
- **Backend**: Python 3.13, FastAPI, Uvicorn, Scikit-learn, WebSockets, PyJWT, SQLite
- **Frontend**: React 19, TypeScript, Vite, Tailwind CSS, Leaflet, React-Leaflet, Recharts, Lucide Icons
- **Dataset**: Authentic New York MTA Subway Network Infrastructure (Geospatial coordinates, route lines, station capacities, hourly ridership distributions)
