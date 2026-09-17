# MetroFlow — Feature Implementation & Data Honesty Report

**Date of Audit:** September 2026  
**Auditor Role:** Senior AI/ML Systems Engineer  
**Audit Purpose:** Comprehensive codebase inspection, architecture audit, and data provenance verification for academic/mentor evaluation.  
**Constraint Adherence:** Read-only technical inspection. No source files or configurations were modified.

---

## 1. Executive Summary & Verification Matrix

The core machine learning asset of the MetroFlow repository is a single **Random Forest Regressor** artifact (`crowd_prediction_rf_compressed.pkl`), trained on historical Seoul Metropolitan Subway ridership data (`seoul_metro_merged_clean.csv`, ~6M rows, 2015–2017, 275 stations, 8 lines) with an empirical evaluation of $R^2 = 0.9519$. 

The model's **sole ground-truth prediction target is crowd volume (`total_flow`)**, mapped to an 11-dimensional spatio-temporal feature vector (`station_code`, `line_num`, `year`, `hour`, `day_of_week`, `is_weekend`, `month`, `is_morning_peak`, `is_evening_peak`, `latitude`, `longitude`).

The table below provides an overview of what is backed by this real ML model versus what is implemented using mathematical equations, rule-based heuristics, or synthetic data.

| Feature | Implementation Status | Core Technical Method | Underlying Data Source |
| :--- | :---: | :--- | :--- |
| **1. Scheduling Management** *(Frequency Optimization & Timetable Adjustments)* | **Partially** | **Rule-Based Heuristic Logic** (4-tier threshold boundaries based on crowd density) | ML-predicted density or heuristic curve; **No train schedule or physical capacity data** |
| **2. Alert & Notification Engine** *(Overcrowding & Congestion Warnings)* | **Partially** | **Rule-Based Threshold Scanner** with 15-min deduplication window & console mock dispatch | ML-predicted density; **No live sensor telemetry or real push notification gateway** |
| **3. Delay Impact Prediction** *(Downstream Delay Propagation)* | **Partially** | **Mathematical Exponential Decay Formula** ($\Delta t_k = \Delta t_0 \times \text{decay}^k$) | **Purely synthetic user input**; **No empirical train delay dataset** |
| **4. Ticketing / Sensor-Based Density Tracking** *(Historical Turnstiles & Train Occupancy)* | **Partially** | **Synthetic Double-Gaussian Curve Generator** (`seed.py`) stored in relational tables | **100% Synthetically Generated Data**; **Not from the real 6M-row ridership CSV** |

---

## 2. In-Depth Feature Audit

---

### Feature 1: Scheduling Management (Train Frequency Optimization & Headways)

#### a) Is this feature currently implemented?
**Partially.** The API provides an endpoint that accepts a station code, evaluates the predicted crowd density, and returns a recommended action string and headway number. However, it does not interface with actual physical train dispatchers, signaling blocks, or rolling-stock availability constraints.

#### b) Where is it implemented?
- **Backend Service:** `recommend_frequency` in `backend/app/services/scheduling.py` (lines 15–53)
- **Placeholder Service:** `recommend_frequency` in `backend/app/services/schedule_service.py` (lines 1–14)
- **API Route:** `get_schedule_recommendation` (`GET /api/v1/schedule/recommend/{station_code}`) in `backend/app/routers/schedule.py` (lines 16–50)
- **Frontend UI:** `frontend/src/pages/SchedulePage.tsx`

#### c) How does it work technically?
It is **strictly simple if-then-else threshold rule logic**. 
- It evaluates the platform density metric (either generated from the ML model or the heuristic fallback) against fixed constants:
  - $\text{Density} < 40\%$: "Maintain current schedule" (urgency: low)
  - $40\% \le \text{Density} < 68\%$: "Monitor; no change needed yet" (urgency: medium)
  - $68\% \le \text{Density} < 86\%$: "Increase frequency by 2 trains/hour" (urgency: high)
  - $\text{Density} \ge 86\%$: "Increase frequency by 4 trains/hour and flag for operator review" (urgency: critical)
- In the frontend (`SchedulePage.tsx`, lines 50–68), base frequency is hardcoded to 12 trains/hour (5.0 min headway) and statically adjusted to 16 trains/hr (3.5 min), 14 trains/hr (4.0 min), or 10 trains/hr (6.0 min).

#### d) What data does it use?
It uses the output of the crowd prediction model or the fallback heuristic density value. It uses **no operational train scheduling data**, **no rolling-stock constraints**, and **no line capacity data**.

#### e) Synthetic data generation & separation
No direct synthetic dataset is ingested; it executes purely on runtime threshold checks against the predicted density score.

#### f) Accuracy & performance claims
- **Claim in README / UI:** Mentions "Dynamic Headway Optimization Algorithm" and "Automated AI Scheduling Optimization".
- **Honesty Assessment:** There is **no ML optimization algorithm** (such as Mixed-Integer Linear Programming, Reinforcement Learning, or Genetic Algorithms) solving headway dispatching. The recommendations are deterministic rule-based lookups.

#### g) Limitations
- Cannot schedule trains dynamically based on fleet availability, track interlocking, power constraints, or crew shifts.
- Cannot optimize bidirectional headway trade-offs.

---

### Feature 2: Alert & Notification Engine (Overcrowding & Incident Warnings)

#### a) Is this feature currently implemented?
**Partially.** An automated alert scanner runs periodically in the background via APScheduler/asyncio, identifies high-density stations, inserts records into the database `alerts` table, and logs dispatch messages to the console.

#### b) Where is it implemented?
- **Scanner Engine:** `check_and_create_alerts` in `backend/app/services/alert_engine.py` (lines 28–94)
- **Background Scheduler:** `start_scheduler` in `backend/app/services/scheduler.py` (lines 50–80)
- **Simulation Dispatch:** `simulate_notification` in `backend/app/services/alert_engine.py` (lines 14–26)
- **API Routes:** `list_alerts`, `resolve_alert` in `backend/app/routers/alerts.py` (lines 14–72)
- **Database Model:** `Alert` in `backend/app/models/alert.py` (lines 8–29)
- **Frontend UI:** `frontend/src/pages/AlertsPage.tsx`

#### c) How does it work technically?
- Every 5 minutes (via APScheduler or asyncio background loop), the engine queries all stations in the SQLite/PostgreSQL `stations` table.
- For each station, it obtains predicted density via `predict_crowd_density()`.
- If the predicted congestion label is `"high"` or `"critical"`, it checks whether an unresolved alert was created within the last 15 minutes (`dedup_window_minutes = 15`).
- If no recent alert exists, an `Alert` record is persisted with an explainable message, and `simulate_notification()` prints an SMS/Push log string to stdout/logger.

#### d) What data does it use?
It evaluates ML model inferences or heuristic fallback scores against station master records. It does **not connect to real SMS gateways (Twilio), WebSockets, Apple APNs, or Firebase Cloud Messaging (FCM)**.

#### e) Synthetic data generation & separation
Initial seed alerts in `seed.py` (lines 411–450) are hardcoded synthetic sample scenarios (e.g. "Platform density exceeded 185 passengers/sqm at Gangnam", "Signal regulation delay at Seoul Station"). They are populated during DB initialization for demonstration purposes.

#### f) Accuracy & performance claims
No statistical ML accuracy claims are made on the alert engine itself; it operates as an operational rule engine on top of crowd density estimates.

#### g) Limitations
- Alerts are generated based on static time/date inferences from the ML model, not live sensor spikes (e.g., unexpected stadium crowd surges or station emergency evacuations cannot be detected unless reflected in normal diurnal patterns).
- Dispatch is simulated via server log outputs, not delivered to passenger mobile apps or SMS.

---

### Feature 3: Delay Impact Prediction (Downstream Delay Propagation)

#### a) Is this feature currently implemented?
**Partially.** An endpoint allows an operator to post a delay incident (e.g., Line 2, Gangnam, 10 minutes) and returns the calculated downstream delay for the next $N$ stations along that track.

#### b) Where is it implemented?
- **Propagation Logic:** `handle_delay` in `backend/app/services/scheduling.py` (lines 55–149)
- **API Route:** `report_delay` (`POST /api/v1/schedule/delay`) in `backend/app/routers/schedule.py` (lines 52–77)
- **Database Model:** `TrainStatus` in `backend/app/models/train_status.py` (lines 7–21)
- **Frontend UI:** `frontend/src/pages/StationDetailPage.tsx` (lines 282–344)

#### c) How does it work technically?
This is a **pure mathematical exponential decay formula**, not a machine learning model.
- Formula implemented:
  $$\text{Delay}_{\text{hop}} = \text{round}\Big(\text{InitialDelay} \times (\text{decay\_rate})^{\text{hop}}, 1\Big)$$
  where default $\text{decay\_rate} = 0.75$, and $\text{hop} \in \{1, 2, 3, 4\}$.
- For circular lines (Line 2), it implements an index wrap-around along ordered station codes.
- When an incident is posted, it also writes a synthetic telemetry row into `train_status` with $\text{occupancy\_pct} = \min(100.0, 50.0 + \text{delay\_minutes} \times 3.5)$.

#### d) What data does it use?
It uses **no empirical delay dataset**. The input is user-supplied parameters (station, line, delay minutes), and the output is calculated directly from the decay formula.

#### e) Synthetic data generation & separation
Initial rows in `train_status` in `seed.py` (lines 367–404) are generated synthetically using Gaussian curve weights and random 5% delay injections.

#### f) Accuracy & performance claims
- **Claim in README:** README Section 7 claims: *"Delay Propagation Accuracy: Target $\pm 1.5$ min, Achieved $\pm 0.8$ min downstream variance"*.
- **Honesty Assessment:** **Misleading.** Because there was no historical train delay dataset or trained ML model for delay propagation, this metric does not represent an empirical validation error on real train operational logs; it is a synthetic theoretical parameter.

#### g) Limitations
- Cannot model real train physics (acceleration, deceleration, signal aspects, track block occupancy, headway buffering, junction conflicts, or crew changes).
- Assumes an arbitrary constant decay rate ($0.75$) regardless of station dwell times or passenger exchange volumes.

---

### Feature 4: Ticketing / Sensor-Based Density Tracking

#### a) Is this feature currently implemented?
**Partially.** The database schema supports historical hourly inflow and outflow logs (`RidershipLog`) and train telemetry (`TrainStatus`), and the API serves historical time-series endpoints (`/stations/{code}/history` and `/analytics/overview`). However, **the data populating these tables in the running application is 100% synthetically generated via mathematical equations in `seed.py`**.

#### b) Where is it implemented?
- **Synthetic Curve Equation:** `compute_ridership_gaussian_curve` in `backend/app/db/seed.py` (lines 173–224)
- **Database Seeder:** `seed_database` in `backend/app/db/seed.py` (lines 226–450)
- **Database Models:** `RidershipLog` in `backend/app/models/ridership.py`, `TrainStatus` in `backend/app/models/train_status.py`
- **Analytics Routes:** `get_station_history`, `get_analytics_overview` in `backend/app/routers/analytics.py`
- **Frontend UI:** `frontend/src/pages/StationDetailPage.tsx` (lines 183–280, Recharts Inflow/Outflow Area Chart), `frontend/src/pages/AnalyticsPage.tsx`

#### c) How does it work technically?
- When the backend initializes, `seed_database()` checks if `ridership_logs` is populated.
- If empty, it synthesizes 14 days of hourly records ($14 \times 24 = 336$ data points per station) across all stations using a **Double-Gaussian mathematical function**:
  - **Weekday Inflow:**
    $$G_{\text{am}} = 1.35 \times \exp\left(-\frac{(h - 8.2)^2}{2 \times 1.2^2}\right)$$
    $$G_{\text{pm}} = 1.40 \times \exp\left(-\frac{(h - 18.3)^2}{2 \times 1.3^2}\right)$$
    $$G_{\text{mid}} = 0.35 \times \exp\left(-\frac{(h - 12.5)^2}{2 \times 1.5^2}\right)$$
  - **Weekend Inflow:** Unimodal curve centered at 15:12 PM ($G_{\text{wknd}} = 0.88 \times \exp(-\frac{(h-15.2)^2}{2 \times 3.6^2})$).
  - Stochastic multiplicative noise ($\text{random.uniform}(0.90, 1.10)$) is added to simulate natural variance.
- Base capacity is assigned as 3,600 for major transfer hubs (`150`, `222`, `239`, `216`, `318`, `1004`, `514`, `208`, `212`, `916`) and 1,200 for regular stations.

#### d) What data does it use?
- The database tables and charting feeds are **not queried from the 6M-row `seoul_metro_merged_clean.csv` file**. 
- The 6M-row CSV was used **offline to train the pickled Random Forest model**. The operational database uses the generated synthetic time-series described above.

#### e) Synthetic data generation & separation
- **Is it flagged in the UI?** In `StationDetailPage.tsx` (line 191), the subtitle states *"Empirical and simulated Seoul Metro ridership distributions"*.
- **Code Separation:** In `seed.py`, line 303 explicitly prints: `"[2/4] Generating synthetic ridership time-series logs..."`.

#### f) Accuracy & performance claims
No accuracy metric ($R^2$ or RMSE) applies directly to the database time-series logs since they are procedurally generated by the Gaussian function.

#### g) Limitations
- Does not reflect real-time smart card turnstile taps or live weight-sensor IoT readings.
- Special events (e.g., concerts at Olympic Park, protests at Gwanghwamun, adverse weather anomalies) are not represented.

---

## 3. Language & Claim Audit

The following table details instances in documentation, code comments, and UI strings where language overstates actual capabilities, along with clear recommendations for academic and technical honesty.

| File / Location | Exact Text or Claim Found | Why It Is Misleading | Suggested Honest Technical Rewording |
| :--- | :--- | :--- | :--- |
| **README.md**<br>`Lines 137–142` | *"Operational & Sensor Datasets Ingested: Smart Card (AFC) Data, Train GPS & Telemetry Data, Car-level passenger weight sensor readings"* | Implies the live platform ingests real-time IoT weight sensors and live GPS streams. In reality, only historical ridership data was used for offline ML training, and active telemetry in the DB is synthetically seeded. | *"Data Architecture: Trained on historical Smart Card ridership logs; operational runtime uses simulated sensor telemetry and synthetic time-series distributions."* |
| **README.md**<br>`Line 188` | *"Dynamic Headway Optimization Algorithm"* | Describes a simple 4-tier if-else threshold rule as an optimization algorithm. | *"Rule-Based Headway Recommendation Engine"* |
| **README.md**<br>`Line 247` | *"Crowd Density Estimation Error: RMSE = 4.2% on validation splits"* | Uses percentage density notation rather than passenger volume count ($R^2 = 0.9519$ on `total_flow`). | *"Volume Prediction Performance: $R^2 = 0.9519$, evaluated on historical validation test splits for station passenger flow."* |
| **README.md**<br>`Line 248` | *"Delay Propagation Accuracy: $\pm 0.8\text{ min}$ downstream variance"* | Implies an ML model was validated against real delayed train records, when it is purely an analytical exponential formula. | *"Downstream Delay Model: Analytical exponential decay formulation ($\text{decay} = 0.75$) for operational impact simulation."* |
| **SchedulePage.tsx**<br>`Line 101` | *"AI Train Scheduling & Dispatch Optimization"* | The scheduling page recommendations are rule-based lookups mapped from crowd density, not an AI optimization model. | *"Data-Driven Train Frequency & Headway Dispatch Recommendations"* |
| **SchedulePage.tsx**<br>`Line 183` | *"AI Recommended [Frequency / Headway]"* | The headway number is derived from a hardcoded switch-case on congestion label, not an AI model. | *"Rule-Based Dispatch Recommendation"* |
| **StationDetailPage.tsx**<br>`Line 158` | *"AI Headway Dispatch Recommendation"* and *"XAI Reasoning"* | The "reasoning" string is an if-else template string explaining which threshold was crossed, not Explainable AI (SHAP/LIME). | *"Threshold-Based Headway Recommendation & Rule Context"* |
| **StationDetailPage.tsx**<br>`Line 89` | *"Retrieving real-time station telemetry and ridership history..."* | Data returned from `/stations/{code}/history` is generated by the synthetic double-Gaussian curve seeder. | *"Retrieving simulated station history and diurnal ridership profiles..."* |
| **LiveMapPage.tsx**<br>`Line 28` | *"Real-time platform overcrowding thresholds and automated dispatch notifications"* | The alerts are triggered from ML model time predictions on current clock time, not live turnstile counts. | *"Scheduled predictive overcrowding threshold scanner and simulated dispatch logs."* |
| **model_loader.py**<br>`Line 134` | *"Physics-informed statistical model matching Seoul Metro empirical patterns"* | The fallback is a double-Gaussian diurnal curve, not a differential equations physics model. | *"Empirical double-Gaussian diurnal curve matching standard transit peak-hour patterns."* |

---

## 4. Ground-Truth Machine Learning vs. Heuristic Demarcation

To provide clear demarcation for academic review or project presentation:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    REAL MACHINE LEARNING ENGINE (GROUND TRUTH)               │
├──────────────────────────────────────────────────────────────────────────────┤
│ • Model Architecture: Scikit-Learn Random Forest Regressor                   │
│ • Training Dataset: Real Seoul Metropolitan Subway Data (~6M rows, 2015–17)  │
│ • Target Variable: total_flow (Ridership Volume / Turnstile Footfall)        │
│ • Validated Performance: R² = 0.9519 on historical validation splits         │
│ • Input Features (11): station_code, line_num, year, hour, day_of_week,     │
│   is_weekend, month, is_morning_peak, is_evening_peak, latitude, longitude   │
│ • Artifact File: crowd_prediction_rf_compressed.pkl (1.01 GB)                │
└──────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│             ANALYTICAL FORMULAS, RULE ENGINES & SYNTHETIC DATA               │
├──────────────────────────────────────────────────────────────────────────────┤
│ • Congestion Classification: Rule-based binning (0-40 Low, 40-68 Med, etc.) │
│ • Train Headway Recommendations: If-else expert rule lookup                  │
│ • Delay Propagation: Analytical exponential decay (Delay_0 * 0.75^k)         │
│ • Alert Notifications: Periodic database cron scanner with mock log outputs  │
│ • Inflow / Outflow Charts: Synthetic Double-Gaussian time-series (seed.py)   │
│ • Train Status / Occupancy: Synthetic random telemetry simulation            │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Conclusion & Recommendations

1. **Strong Core ML Asset:** The ridership prediction model is a legitimate, well-trained Random Forest Regressor trained on real Seoul Subway transit data with strong statistical performance ($R^2 = 0.9519$).
2. **Transparent Academic Positioning:** The platform should be presented as an **AI-driven crowd forecasting engine coupled with an operational decision-support and simulation platform**.
3. **Documentation Cleanup:** Adjust the README and UI copy per Section 3 above so that evaluators and mentors understand the distinction between the trained ML model and the rule-based dispatching/simulation layers.
