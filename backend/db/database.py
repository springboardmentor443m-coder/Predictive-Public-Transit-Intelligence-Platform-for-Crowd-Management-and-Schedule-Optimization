"""
MetroFlow Database & Security Layer
SQLite embedded relational database with pre-seeded Admin and Operator accounts,
schema initialization, password hashing, and operational audit tables.
"""

import sqlite3
import os
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any, List

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "metroflow.db")

def hash_password(password: str) -> str:
    """SHA-256 password hash for deterministic local testing and zero external salt dependency."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        name TEXT NOT NULL,
        role TEXT NOT NULL, -- 'admin' or 'operator'
        title TEXT NOT NULL,
        badge_id TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP
    );
    """)

    # Alerts & Notifications table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        severity TEXT NOT NULL, -- 'info', 'warning', 'critical', 'emergency'
        category TEXT NOT NULL, -- 'overcrowding', 'delay', 'emergency', 'maintenance'
        station_id TEXT,
        station_name TEXT,
        line TEXT,
        message TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN DEFAULT 1,
        resolved_by TEXT
    );
    """)

    # Train Schedules & Frequency Settings table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS line_schedules (
        line TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        color TEXT NOT NULL,
        current_headway REAL NOT NULL,
        recommended_headway REAL NOT NULL,
        peak_status TEXT NOT NULL, -- 'Peak' or 'Standard'
        active_train_count INTEGER NOT NULL,
        status TEXT NOT NULL, -- 'On-Time', 'Minor Delay', 'Severe Delay'
        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Operational Audit Logs table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS operational_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_name TEXT NOT NULL,
        role TEXT NOT NULL,
        action TEXT NOT NULL,
        details TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Pre-seed Admin and Operator users if not present
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO users (email, password_hash, name, role, title, badge_id)
        VALUES 
        ('admin@metroflow.ny', ?, 'Sarah Chen', 'admin', 'Chief Transit Director', 'NY-ADM-01'),
        ('operator@metroflow.ny', ?, 'Marcus Rivera', 'operator', 'Operations Rail Dispatcher', 'NY-OPS-88')
        """, (hash_password("admin123"), hash_password("operator123")))

    # Pre-seed Line Schedules
    from data.nyc_subway_data import NYC_SUBWAY_LINES
    cursor.execute("SELECT COUNT(*) FROM line_schedules")
    if cursor.fetchone()[0] == 0:
        for line_id, data in NYC_SUBWAY_LINES.items():
            cursor.execute("""
            INSERT INTO line_schedules (line, name, color, current_headway, recommended_headway, peak_status, active_train_count, status)
            VALUES (?, ?, ?, ?, ?, 'Standard', ?, 'On-Time')
            """, (line_id, data["name"], data["color"], data["headway_mins"], data["headway_mins"], 8))

    # Pre-seed realistic active alerts
    cursor.execute("SELECT COUNT(*) FROM alerts")
    if cursor.fetchone()[0] == 0:
        sample_alerts = [
            ("critical", "overcrowding", "NYC-TSQ42", "Times Sq - 42 St", "1", "High platform passenger accumulation detected on Downtown Platform. Headway reduction advised."),
            ("warning", "delay", "NYC-GCT42", "Grand Central - 42 St", "4", "Signal sequencing delay near 42nd St causing 3-minute dwell extension on Line 4."),
            ("emergency", "emergency", "NYC-PENN34", "34 St - Penn Station", "A", "Track debris alert reported on Uptown local track. Speed restriction enforced.")
        ]
        for sev, cat, st_id, st_name, line, msg in sample_alerts:
            cursor.execute("""
            INSERT INTO alerts (severity, category, station_id, station_name, line, message, is_active)
            VALUES (?, ?, ?, ?, ?, ?, 1)
            """, (sev, cat, st_id, st_name, line, msg))

    conn.commit()
    conn.close()

init_db()
