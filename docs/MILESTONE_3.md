# Milestone 3 — Weeks 5 & 6: Real-Time Monitoring, Alerts & Schedule Optimization

> PRD scope: Implement real-time crowd monitoring using live data feeds · Develop
> automated alert system for overcrowding and delays · Build schedule optimization
> engine based on AI predictions · Integrate alert notifications with dashboard.

## 1. Real-Time Crowd Monitoring

- **Socket.IO channel** (`app/services/realtime.py`): background loop every 10s
  broadcasts `crowd_update` events with all station snapshots to the dashboard.
- Snapshot pipeline: DB ridership + Redis-cached latest values (`crowd:latest:{sid}`,
  30s TTL) → `app/core/cache.py` (in-memory fallback when Redis is absent).
- Sensor ingestion: density snapshots are sampled into MongoDB
  (`log_sensor_event`, 20% sample) so raw event history accumulates for auditing.
- Frontend subscribes via `lib/socket.js`; Overview/Crowd pages update KPIs, station
  cards and heatmap tiles without refresh.

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
| Real-time monitoring functional with live data feed | ✅ Socket.IO loop |
| Alert system triggers correctly under congestion scenarios | ✅ rule engine + tests |
| Optimized schedules generated from AI predictions | ✅ optimization + apply endpoint |
| Dashboard displays alerts and updated schedules | ✅ |

## Outcomes (PRD)

Gained experience integrating real-time data streams; implemented event-driven backend
logic; strengthened full-stack integration skills across WebSocket, REST and UI.
