# Milestone 3 — Weeks 5 & 6: Real-Time Monitoring, Alerts & Schedule Optimization

> PRD scope: Implement real-time crowd monitoring using live data feeds · Develop
> automated alert system for overcrowding and delays · Build schedule optimization
> engine based on AI predictions · Integrate alert notifications with dashboard.

## 1. Real-Time Crowd Monitoring

- **Socket.IO channel** (`app/services/realtime.py`): background loop every 5s
  broadcasts `crowd_update` events (global + per-station `station:{id}` rooms)
  with all station snapshots to the dashboard. Clients authenticate via
  Socket.IO `auth.token` (JWT, optional) and join rooms with
  `join_station` / `leave_station`.
- Snapshot pipeline: DB ridership + Redis-cached latest values (`crowd:latest:{sid}`,
  30s TTL) → `app/core/cache.py` (in-memory fallback when Redis is absent).
- Sensor ingestion: density snapshots are sampled into MongoDB
  (`log_sensor_event`, 20% sample) so raw event history accumulates for auditing.
- Frontend subscribes via `lib/socket.js`; Overview/Crowd pages update KPIs, station
  cards and heatmap tiles without refresh.

## 1b. Real-Time Train Monitoring

- **Live fleet layer** (`app/services/train_monitor.py`): derives telemetry per train
  from the timetable engine — status (`in_transit` / `at_station` / `delayed` /
  `awaiting_departure` / `in_depot` / `at_terminal` / `out_of_service`), position %
  between stops, current/next station, ETA, headway, delay minutes, and a projected
  `load_pct` from the cached crowd snapshots (`crowd:latest:{sid}`). 45 s dwell,
  3 h lookback / 18 h lookahead schedule windows.
- **Socket.IO extension**: the realtime loop now also broadcasts `train_update`
  (global + per-train `train:{id}` rooms); clients join/leave with
  `join_train` / `leave_train` room handlers.
- **REST surface** (`app/api/v1/trains.py`): `GET /trains` (fleet list),
  `GET /trains/live` (full live telemetry), `GET /trains/live/{train_id}`, and
  `GET /trains/{train_id}/schedule` (upcoming stops).
- **Per-train forecasts**: `GET /predictions/train/{train_id}?hours=N` returns the
  expected crowd occupancy & passenger demand at each upcoming stop of the train.
- Frontend: `pages/dashboard/trains.jsx` (live fleet cards, per-train detail KPIs,
  upcoming-stops table + per-stop forecast chart), overview fleet strip on
  `pages/dashboard/index.jsx`, and `lib/socket.js` `joinTrainRoom`/`leaveTrainRoom`.

## 2. Automated Alert System

Rule engine in `app/services/alert_service.py::evaluate_alerts()`:

| Rule | Condition | Severity |
|---|---|---|
| Overcrowding | occupancy ≥ 90% | high |
| Critical overcrowding | occupancy ≥ 100% | critical |
| Delay notification | schedule delayed > 2 min (raised by delay report) | medium |

- Deduplication: one open alert per (station, type) within a 15-minute window.
- The engine runs inside the realtime loop each cycle; fresh alerts are pushed on the
  `alert_event` socket channel exactly once (`recent_unbroadcast_alerts`).
- Delay workflow: `POST /scheduling/delay/{schedule_id}` updates the timetable AND
  creates the notification alert (returns `alert_id`) — verified by
  `test_delay_creates_notification_alert`.
- Acknowledge flow: `POST /alerts/{id}/acknowledge` (operator/admin).
- Emergency broadcast console: admin-only `POST /alerts/broadcast` → persisted alert +
  instant socket push; UI in `pages/dashboard/alerts.jsx`.

## 3. Schedule Optimization Engine

- Optimization service `app/services/scheduling_service.py::optimize_schedules()`:
  compares predicted peak load vs. scheduled capacity per station and produces
  recommendations (increase/decrease frequency, add capacity).
- Smart recommendations: `/predictions/recommendations` → suggested headway per station.
- **Frequency adjustment execution**: `POST /scheduling/apply-headway/{station_id}`
  applies the AI-recommended (or explicit) headway to all future schedules of that
  station — closes the loop from insight to action. Verified by
  `test_apply_headway_frequency_adjustment`.
- Timetable CRUD + delay reporting UI: `pages/dashboard/scheduling.jsx` with an
  "Apply" button on each optimizer card.

## 4. Dashboard Integration

- Alerts feed with severity chips + filters; unread badge in sidebar.
- Live toast/banner on incoming `alert_event` socket messages.
- Scheduling page reflects applied headways immediately after Apply.

## Evaluation Criteria Checkpoint (PRD §6, Week 6)

| Criterion | Status |
|---|---|
| Real-time monitoring functional with live data feed | ✅ Socket.IO loop (crowd + train) |
| Train position/status tracking meets PRD | ✅ /trains/live + train_update events |
| Alert system triggers correctly under congestion scenarios | ✅ rule engine + tests |
| Optimized schedules generated from AI predictions | ✅ optimization + apply endpoint |
| Dashboard displays alerts and updated schedules | ✅ |

## Outcomes (PRD)

Gained experience integrating real-time data streams; implemented event-driven backend
logic; strengthened full-stack integration skills across WebSocket, REST and UI.
