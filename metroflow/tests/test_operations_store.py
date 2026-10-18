import json
from app.services import operations_store


def test_snapshot_history_persists_and_returns_latest_first(monkeypatch, tmp_path):
    monkeypatch.setattr(operations_store, "DB_PATH", tmp_path / "ops.db")
    summary = {
        "tick": 1, "updated_at": "2026-10-15T10:00:00+00:00", "scenario": "normal",
        "system_total_entries": 1200, "system_total_exits": 1100,
        "high_crowd_stations": 2, "critical_stations": 0, "alert_count": 1,
    }
    stations = [{"station": "Example", "entries": 1200}]
    alerts = [{"station": "Example", "severity": "Moderate"}]
    operations_store.save_snapshot(summary, stations, alerts)
    history = operations_store.history(10)
    assert len(history) == 1
    assert history[0]["system_total_entries"] == 1200
    latest = operations_store.latest_snapshot()
    assert latest["stations"] == stations
    assert latest["alerts"] == alerts


def test_event_log_records_scenario_changes(monkeypatch, tmp_path):
    monkeypatch.setattr(operations_store, "DB_PATH", tmp_path / "ops.db")
    operations_store.record_event("scenario_changed", "demand_surge", {"previous_scenario": "normal"})
    events = operations_store.events(10)
    assert len(events) == 1
    assert events[0]["event_type"] == "scenario_changed"
    assert events[0]["details"]["previous_scenario"] == "normal"
