"""Persistent SQLite history for MetroFlow's explicitly simulated operations feed."""
from __future__ import annotations
import json
import os
import sqlite3
from pathlib import Path
from typing import Any

DB_PATH = Path(os.getenv("METROFLOW_DB_PATH", str(Path(__file__).resolve().parents[1] / "data" / "metroflow_ops.db")))


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH, timeout=10)
    con.row_factory = sqlite3.Row
    return con


def init_db() -> None:
    with _connect() as con:
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("""CREATE TABLE IF NOT EXISTS simulation_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tick INTEGER NOT NULL,
            updated_at TEXT NOT NULL,
            scenario TEXT NOT NULL,
            total_entries INTEGER NOT NULL,
            total_exits INTEGER NOT NULL,
            high_crowd_stations INTEGER NOT NULL,
            critical_stations INTEGER NOT NULL,
            alert_count INTEGER NOT NULL,
            stations_json TEXT NOT NULL,
            alerts_json TEXT NOT NULL
        )""")
        con.execute("CREATE INDEX IF NOT EXISTS idx_sim_snapshots_updated ON simulation_snapshots(updated_at DESC)")
        con.execute("""CREATE TABLE IF NOT EXISTS operations_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            event_type TEXT NOT NULL,
            scenario TEXT NOT NULL,
            details TEXT NOT NULL
        )""")


def save_snapshot(summary: dict[str, Any], stations: list[dict], alerts: list[dict]) -> None:
    init_db()
    with _connect() as con:
        con.execute("""INSERT INTO simulation_snapshots
          (tick,updated_at,scenario,total_entries,total_exits,high_crowd_stations,critical_stations,alert_count,stations_json,alerts_json)
          VALUES (?,?,?,?,?,?,?,?,?,?)""", (
            int(summary["tick"]), str(summary["updated_at"]), str(summary["scenario"]),
            int(summary["system_total_entries"]), int(summary["system_total_exits"]),
            int(summary["high_crowd_stations"]), int(summary["critical_stations"]), int(summary["alert_count"]),
            json.dumps(stations, separators=(",", ":")), json.dumps(alerts, separators=(",", ":")),
        ))
        # Keep a bounded local database rather than allowing an unattended demo to grow forever.
        con.execute("DELETE FROM simulation_snapshots WHERE id NOT IN (SELECT id FROM simulation_snapshots ORDER BY id DESC LIMIT 10000)")


def record_event(event_type: str, scenario: str, details: dict[str, Any]) -> None:
    from datetime import datetime, timezone
    init_db()
    with _connect() as con:
        con.execute("INSERT INTO operations_events(created_at,event_type,scenario,details) VALUES(?,?,?,?)",
                    (datetime.now(timezone.utc).isoformat(), event_type, scenario, json.dumps(details, separators=(",", ":"))))
        con.execute("DELETE FROM operations_events WHERE id NOT IN (SELECT id FROM operations_events ORDER BY id DESC LIMIT 2000)")


def history(limit: int = 100) -> list[dict[str, Any]]:
    init_db()
    limit = max(1, min(int(limit), 500))
    with _connect() as con:
        rows = con.execute("SELECT id,tick,updated_at,scenario,total_entries AS system_total_entries,total_exits AS system_total_exits,high_crowd_stations,critical_stations,alert_count FROM simulation_snapshots ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [dict(row) for row in reversed(rows)]


def latest_snapshot() -> dict[str, Any] | None:
    init_db()
    with _connect() as con:
        row = con.execute("SELECT * FROM simulation_snapshots ORDER BY id DESC LIMIT 1").fetchone()
    if not row:
        return None
    item = dict(row)
    item["stations"] = json.loads(item.pop("stations_json"))
    item["alerts"] = json.loads(item.pop("alerts_json"))
    return item


def events(limit: int = 100) -> list[dict[str, Any]]:
    init_db()
    limit = max(1, min(int(limit), 500))
    with _connect() as con:
        rows = con.execute("SELECT id,created_at,event_type,scenario,details FROM operations_events ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item["details"] = json.loads(item["details"])
        result.append(item)
    return result
