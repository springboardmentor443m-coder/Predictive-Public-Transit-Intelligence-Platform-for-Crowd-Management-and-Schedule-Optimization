import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.base import Base
from app.models.station import Station
from app.models.alert import Alert
from app.models.user import User
from app.core.security import get_password_hash
from app.services.alert_engine import check_and_create_alerts, simulate_notification


@pytest.fixture
def alert_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    session = TestingSession()
    # Seed stations: Gangnam (major hub with high density) and a quiet station
    stations = [
        Station(station_code="222", name_en="Gangnam", line="Line 2", latitude=37.49, longitude=127.02, district="Gangnam-gu"),
        Station(station_code="239", name_en="Hongik Univ.", line="Line 2", latitude=37.55, longitude=126.92, district="Mapo-gu"),
        Station(station_code="819", name_en="Bokjeong", line="Line 8", latitude=37.47, longitude=127.12, district="Songpa-gu"),
    ]
    session.add_all(stations)
    session.commit()
    
    yield session
    session.close()


def test_simulate_notification(alert_db, capsys):
    alert = Alert(
        station_code="222",
        alert_type="overcrowding",
        severity="critical",
        message="Critical platform congestion detected at Gangnam.",
        created_at=datetime.now(timezone.utc),
        resolved=False,
    )
    simulate_notification(alert)
    captured = capsys.readouterr()
    assert "[NOTIFY]" in captured.out
    assert "CRITICAL" in captured.out
    assert "Gangnam" in captured.out


def test_check_and_create_alerts_and_deduplication(alert_db):
    # 1. First execution: scans and creates alerts for busy stations
    new_alerts = check_and_create_alerts(alert_db, dedup_window_minutes=15)
    assert isinstance(new_alerts, list)
    
    # Verify alerts exist in DB
    all_alerts = alert_db.execute(select(Alert)).scalars().all()
    assert len(all_alerts) == len(new_alerts)
    for alert in all_alerts:
        assert alert.alert_type == "overcrowding"
        assert alert.severity in ["high", "critical"]
        assert alert.resolved is False

    # 2. Second immediate execution: deduplication window suppresses duplicate alerts
    second_run_alerts = check_and_create_alerts(alert_db, dedup_window_minutes=15)
    assert len(second_run_alerts) == 0, "Deduplication window should prevent duplicate alerts on consecutive runs"

    # Total alerts count in DB remains unchanged
    total_after_second_run = alert_db.execute(select(Alert)).scalars().all()
    assert len(total_after_second_run) == len(all_alerts)


def test_alert_creation_after_resolution(alert_db):
    # Run scan to create initial alerts
    initial_alerts = check_and_create_alerts(alert_db, dedup_window_minutes=15)
    
    if initial_alerts:
        target_alert = initial_alerts[0]
        # Operator resolves the alert
        target_alert.resolved = True
        alert_db.commit()

        # Run scan again: Because existing alert was resolved, a new alert is created if surge continues
        fresh_alerts = check_and_create_alerts(alert_db, dedup_window_minutes=15)
        assert any(a.station_code == target_alert.station_code for a in fresh_alerts)
