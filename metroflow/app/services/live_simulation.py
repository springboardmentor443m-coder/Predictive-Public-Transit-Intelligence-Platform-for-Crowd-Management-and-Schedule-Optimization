"""Clearly labelled simulated-live passenger feed for demos without a transit API.

This module does not claim to provide real-world live data. It samples each station's
historical hourly profile, applies rush-hour and random variation, and keeps a small
in-memory snapshot while the demo is running.
"""
from __future__ import annotations

import random
import threading
from functools import lru_cache
import time
from datetime import datetime, timezone
from typing import Any

from app.data import repository as repo
from app.services import operations_store

_LOCK = threading.RLock()
_STATE: dict[str, Any] = {
    "running": False,
    "started_at": None,
    "last_updated_monotonic": 0.0,
    "updated_at": None,
    "tick": 0,
    "stations": [],
    "alerts": [],
    "interval_seconds": 5,
    "scenario": "normal",
    "history": [],
}


def _rush_factor(hour: int) -> float:
    """Simple demo curve: stronger demand during morning/evening peaks."""
    if 7 <= hour <= 9:
        return 1.35
    if 17 <= hour <= 19:
        return 1.45
    if 10 <= hour <= 16:
        return 0.95
    if 20 <= hour <= 22:
        return 0.75
    return 0.45


@lru_cache(maxsize=1)
def _profiles() -> dict[str, dict[int, tuple[float, float]]]:
    result = {}
    for station in repo.list_stations():
        profile = repo.hourly_profile(station)
        result[station] = {int(row["Hour"]): (float(row["Entries"]), float(row["Exits"])) for _, row in profile.iterrows()}
    return result


def _make_snapshot(tick: int, scenario: str = "normal") -> tuple[list[dict], list[dict]]:
    now = datetime.now().astimezone()
    hour = now.hour
    # A deterministic seed per tick makes each response reproducible in debugging,
    # while successive ticks still produce visible movement in the dashboard.
    rng = random.Random((now.date().toordinal() * 100000) + tick)
    rows: list[dict] = []
    alerts: list[dict] = []
    profiles = _profiles()
    for station in repo.list_stations():
        avg_entries, avg_exits = profiles.get(station, {}).get(hour, (0.0, 0.0))
        baseline = max(0.0, avg_entries * _rush_factor(hour))
        # Small variation simulates changing counts. Occasional surge is explicitly
        # synthetic and intended to exercise congestion/anomaly alerts in demos.
        surge = 1.0
        scenario_multiplier = {
            "normal": 1.0,
            "rush_hour": 1.35,
            "demand_surge": 1.75,
            "service_disruption": 1.15,
        }.get(scenario, 1.0)
        if scenario == "demand_surge" and station == repo.list_stations()[tick % len(repo.list_stations())]:
            scenario_multiplier *= 1.25
        # Keep a small recurring synthetic surge to exercise alerts during demos.
        if scenario == "normal" and tick > 1 and tick % 17 == 0:
            surge = 1.65
        variation = rng.uniform(0.88, 1.12)
        entries = max(0, int(round(baseline * variation * surge * scenario_multiplier)))
        exits = max(0, int(round(avg_exits * _rush_factor(hour) * rng.uniform(0.88, 1.12))))
        capacity = repo.get_capacity(station)
        congestion = round(min(100.0, entries / max(1, capacity) * 100), 1)
        row = {
            "station": station,
            "entries": entries,
            "exits": exits,
            "net_flow": entries - exits,
            "capacity": capacity,
            "congestion_pct": congestion,
            "hour": hour,
            "baseline_entries": int(round(baseline)),
            "is_simulated": True,
            "scenario": scenario,
            "delay_minutes": (8 + (tick % 8)) if scenario == "service_disruption" and station == repo.list_stations()[tick % len(repo.list_stations())] else 0,
        }
        rows.append(row)
        if row["delay_minutes"] > 0:
            alerts.append({
                "station": station, "type": "SIMULATED_SERVICE_DISRUPTION", "severity": "High",
                "message": f"Simulated service disruption: estimated delay {row['delay_minutes']} minutes. This is demo data.",
                "congestion_pct": congestion, "delay_minutes": row["delay_minutes"],
            })
        if congestion >= 85:
            alerts.append({
                "station": station, "type": "SIMULATED_CONGESTION",
                "severity": "Critical" if congestion >= 95 else "High",
                "message": f"Simulated capacity utilisation is {congestion:.1f}%. Review crowd-management options.",
                "congestion_pct": congestion,
            })
        elif baseline >= 20 and entries >= baseline * 1.5:
            alerts.append({
                "station": station, "type": "SIMULATED_DEMAND_SURGE", "severity": "Moderate",
                "message": f"Simulated demand is unusually high versus this hour's baseline ({entries} vs {int(baseline)} entries).",
                "congestion_pct": congestion,
            })
    rows.sort(key=lambda item: item["congestion_pct"], reverse=True)
    alerts.sort(key=lambda item: item["congestion_pct"], reverse=True)
    return rows, alerts


def start(interval_seconds: int = 5) -> dict:
    interval_seconds = max(3, min(int(interval_seconds), 60))
    with _LOCK:
        _STATE.update({
            "running": True,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "last_updated_monotonic": 0.0,
            "updated_at": None,
            "tick": 0,
            "stations": [],
            "alerts": [],
            "interval_seconds": interval_seconds,
            "scenario": "normal",
            "history": [],
        })
        operations_store.record_event("simulation_started", _STATE["scenario"], {"interval_seconds": interval_seconds})
        _advance(force=True)
        return _public_state()


def stop() -> dict:
    with _LOCK:
        was_running = bool(_STATE["running"])
        _STATE["running"] = False
        if was_running:
            operations_store.record_event("simulation_stopped", _STATE.get("scenario", "normal"), {"tick": _STATE.get("tick", 0)})
        return _public_state()


def _advance(force: bool = False) -> None:
    now_mono = time.monotonic()
    if not _STATE["running"]:
        return
    if not force and now_mono - _STATE["last_updated_monotonic"] < _STATE["interval_seconds"]:
        return
    _STATE["tick"] += 1
    stations, alerts = _make_snapshot(_STATE["tick"], _STATE.get("scenario", "normal"))
    _STATE["stations"] = stations
    _STATE["alerts"] = alerts
    _STATE["updated_at"] = datetime.now(timezone.utc).isoformat()
    _STATE["last_updated_monotonic"] = now_mono
    _STATE.setdefault("history", []).append({
        "tick": _STATE["tick"],
        "updated_at": _STATE["updated_at"],
        "scenario": _STATE.get("scenario", "normal"),
        "system_total_entries": sum(row["entries"] for row in stations),
        "system_total_exits": sum(row["exits"] for row in stations),
        "high_crowd_stations": sum(row["congestion_pct"] >= 70 for row in stations),
        "critical_stations": sum(row["congestion_pct"] >= 90 for row in stations),
        "alert_count": len(alerts),
    })
    _STATE["history"] = _STATE["history"][-60:]
    operations_store.save_snapshot(_STATE["history"][-1], stations, alerts)


def _public_state() -> dict:
    stations = list(_STATE["stations"])
    return {
        "running": bool(_STATE["running"]),
        "mode": "SIMULATED_LIVE",
        "is_real_time": False,
        "started_at": _STATE["started_at"],
        "updated_at": _STATE["updated_at"],
        "tick": int(_STATE["tick"]),
        "interval_seconds": int(_STATE["interval_seconds"]),
        "scenario": _STATE.get("scenario", "normal"),
        "feed_status": "running" if _STATE["running"] else "stopped",
        "history": list(_STATE.get("history", [])),
        "station_count": len(stations),
        "system_total_entries": sum(row["entries"] for row in stations),
        "system_total_exits": sum(row["exits"] for row in stations),
        "stations": stations,
        "alerts": list(_STATE["alerts"]),
        "notice": "Simulated demo data derived from historical station profiles; not a real metro feed.",
    }


def get_status() -> dict:
    with _LOCK:
        _advance()
        return _public_state()


def set_scenario(scenario: str) -> dict:
    """Switch the demo scenario without restarting the stream."""
    allowed = {"normal", "rush_hour", "demand_surge", "service_disruption"}
    if scenario not in allowed:
        raise ValueError(f"Unsupported scenario. Choose one of: {', '.join(sorted(allowed))}")
    with _LOCK:
        previous = _STATE.get("scenario", "normal")
        _STATE["scenario"] = scenario
        if previous != scenario:
            operations_store.record_event("scenario_changed", scenario, {"previous_scenario": previous, "new_scenario": scenario})
        if _STATE["running"]:
            _STATE["last_updated_monotonic"] = 0.0
            _advance(force=True)
        return _public_state()
