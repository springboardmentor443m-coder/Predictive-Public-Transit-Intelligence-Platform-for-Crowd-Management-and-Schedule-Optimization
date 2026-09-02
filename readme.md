# MetroFlow — AI Platform for Metro Crowd Management and Scheduling
##: Project Initialization, Design Process & Core Setup

- AI-powered platform to monitor passenger flow, predict crowd density, and optimize train scheduling in real time
- This milestone delivers: project objectives defined, system architecture and DB schema designed, backend set up with FastAPI, JWT authentication with role-based access, and a crowd monitoring API with congestion tracking
- Scheduling, AI forecasting, alerts, and full analytics dashboard are planned for Week 3 onward

**Tech Stack**
- Backend: Python, FastAPI, Uvicorn
- Data: Pandas, NumPy
- Auth: JWT (python-jose), bcrypt
- Reserved for later: scikit-learn

**Dataset**
- Location: `app/data/taipei_mrt_2yr.csv`
- 30 real Taipei Metro stations, hourly data, Jan 2022–Dec 2023
- Schema: Date, Hour, Station, Entries, Exits
- Matches the official data.gov.tw dataset format (#128683) so the real file can be swapped in later with no code changes
- Regenerate with: `python app/data/generate_dataset.py`

**Project Structure**
- `app/main.py` — API routes
- `app/core/security.py` — auth, roles
- `app/data/repository.py` — data access layer
- `app/data/generate_dataset.py` — dataset generator
- `app/data/taipei_mrt_2yr.csv` — dataset
- `app/services/crowd_monitoring.py` — crowd monitoring logic
- `requirements.txt`, `README.md`, `ARCHITECTURE.md`

**Setup**
- `git clone <repo-url>` then `cd metroflow_week1-2`
- (Optional) create a virtual environment: `python -m venv venv`, then activate it
- Install dependencies: `python -m pip install -r requirements.txt`
- Run: `python -m uvicorn app.main:app --reload --port 8000`
- Open docs: `http://127.0.0.1:8000/docs`

**Demo Credentials**
- admin / admin123 — full access
- operator1 / operator123 — station-scoped access
- Login at `POST /auth/login`, copy the token, click Authorize, paste it in

**API Endpoints**
- `POST /auth/login` — log in, get JWT
- `GET /auth/me` — current user profile
- `GET /admin/ping` — admin-only route
- `GET /stations` — list all stations
- `GET /crowd/live` — live congestion, all stations
- `GET /crowd/station/{station}` — single station snapshot
- `GET /crowd/analytics/{station}` — station-wise analytics
- `GET /crowd/heatmap` — congestion heatmap
- `GET /` — root check
- `GET /health` — health/status check

**Architecture**
- Client sends HTTPS + JWT requests to FastAPI (`app/main.py`)
- Routed to User Management (`core/security.py`) or Crowd Monitoring (`services/crowd_monitoring.py`)
- Both read from the Data Repository (`data/repository.py`), backed by the CSV dataset

**Roadmap**
- Milestone 1 (Week 1–2): core setup, auth, crowd monitoring — complete
- Milestone 2 (Week 3–4): scheduling optimization, AI demand forecasting
- Milestone 3 (Week 5–6): alerts, notifications, full analytics dashboard
- Milestone 4 (Week 7–8): testing, deployment, documentation

**Notes**
- Dataset is a realistic stand-in matching the real schema exactly; swap the CSV anytime without code changes
- Default congestion capacity threshold: 6,000 passengers/hour/station, adjustable in `app/data/repository.py`
