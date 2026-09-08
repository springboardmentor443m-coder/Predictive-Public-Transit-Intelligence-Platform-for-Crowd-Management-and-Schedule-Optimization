import sys
from pathlib import Path
import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.base import Base
from app.models.station import Station
from app.models.train_status import TrainStatus
from app.services.scheduling import (
    recommend_frequency,
    handle_delay,
    LOW_CONGESTION_MAX,
    MEDIUM_CONGESTION_MAX,
    HIGH_CONGESTION_MAX,
)
from fastapi import HTTPException


# =========================================================================
# 1. UNIT TESTS: recommend_frequency() Boundary Tests
# =========================================================================

def test_recommend_frequency_low_boundary():
    # Strict boundary below 40%
    res_39 = recommend_frequency(39.9, "low")
    assert res_39["urgency"] == "low"
    assert "maintain current schedule" in res_39["recommended_action"]
    assert "39.9%" in res_39["reason"]

    # 0.0 lower limit
    res_0 = recommend_frequency(0.0, "low")
    assert res_0["urgency"] == "low"
    assert "maintain current schedule" in res_0["recommended_action"]


def test_recommend_frequency_medium_boundary():
    # Exact 40.0% boundary transition
    res_40 = recommend_frequency(40.0, "medium")
    assert res_40["urgency"] == "medium"
    assert "monitor; no change needed yet" in res_40["recommended_action"]
    assert "40.0%" in res_40["reason"]

    # Just below 68.0%
    res_67_9 = recommend_frequency(67.9, "medium")
    assert res_67_9["urgency"] == "medium"
    assert "monitor; no change needed yet" in res_67_9["recommended_action"]


def test_recommend_frequency_high_boundary():
    # Exact 68.0% boundary transition
    res_68 = recommend_frequency(68.0, "high")
    assert res_68["urgency"] == "high"
    assert "increase frequency by 2 trains/hour" in res_68["recommended_action"]
    assert "68.0%" in res_68["reason"]

    # Just below 86.0%
    res_85_9 = recommend_frequency(85.9, "high")
    assert res_85_9["urgency"] == "high"
    assert "increase frequency by 2 trains/hour" in res_85_9["recommended_action"]


def test_recommend_frequency_critical_boundary():
    # Exact 86.0% boundary transition
    res_86 = recommend_frequency(86.0, "critical")
    assert res_86["urgency"] == "critical"
    assert "increase frequency by 4 trains/hour" in res_86["recommended_action"]
    assert "86.0%" in res_86["reason"]

    # 100.0% upper bound
    res_100 = recommend_frequency(100.0, "critical")
    assert res_100["urgency"] == "critical"
    assert "increase frequency by 4 trains/hour" in res_100["recommended_action"]


def test_recommend_frequency_normalized_scale():
    # Handles 0.0 - 1.0 normalized model outputs seamlessly
    res_norm_high = recommend_frequency(0.75, "high")
    assert res_norm_high["urgency"] == "high"
    assert "75.0%" in res_norm_high["reason"]


# =========================================================================
# 2. UNIT TESTS: handle_delay() Propagation & Decay Tests
# =========================================================================

@pytest.fixture
def test_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    session = TestingSession()
    # Seed 4 consecutive stations on Line 2
    stations = [
        Station(station_code="201", name_en="City Hall (L2)", line="Line 2", latitude=37.56, longitude=126.97),
        Station(station_code="202", name_en="Euljiro 1-ga", line="Line 2", latitude=37.56, longitude=126.98),
        Station(station_code="203", name_en="Euljiro 3-ga", line="Line 2", latitude=37.56, longitude=126.99),
        Station(station_code="204", name_en="Euljiro 4-ga", line="Line 2", latitude=37.56, longitude=127.00),
    ]
    session.add_all(stations)
    session.commit()
    
    yield session
    session.close()


def test_handle_delay_propagation_decay(test_db):
    # Incident at station 201 with 10 min delay
    result = handle_delay(
        db=test_db,
        line="Line 2",
        station_code="201",
        delay_minutes=10,
        downstream_count=3,
        decay_rate=0.75,
    )

    assert result["line"] == "Line 2"
    assert result["incident_station_code"] == "201"
    assert result["initial_delay_minutes"] == 10
    
    affected = result["affected_stations"]
    assert len(affected) == 3

    # Hop 1 (202): 10 * 0.75 = 7.5 min
    assert affected[0]["station_code"] == "202"
    assert affected[0]["station_order"] == 1
    assert affected[0]["estimated_delay_minutes"] == 7.5
    assert affected[0]["estimated_eta_delay_seconds"] == 450

    # Hop 2 (203): 10 * (0.75^2) = 5.6 min
    assert affected[1]["station_code"] == "203"
    assert affected[1]["station_order"] == 2
    assert affected[1]["estimated_delay_minutes"] == 5.6

    # Hop 3 (204): 10 * (0.75^3) = 4.2 min
    assert affected[2]["station_code"] == "204"
    assert affected[2]["station_order"] == 3
    assert affected[2]["estimated_delay_minutes"] == 4.2

    # Verify telemetry was written to train_status table
    train_record = test_db.query(TrainStatus).filter(TrainStatus.line == "Line 2").first()
    assert train_record is not None
    assert train_record.delay_minutes == 10


def test_handle_delay_invalid_station(test_db):
    with pytest.raises(HTTPException) as exc_info:
        handle_delay(test_db, line="Line 2", station_code="non_existent_99", delay_minutes=5)
    assert exc_info.value.status_code == 404


def test_handle_delay_mismatched_line(test_db):
    with pytest.raises(HTTPException) as exc_info:
        # Station 201 is on Line 2, querying Line 1 should 404
        handle_delay(test_db, line="Line 1", station_code="201", delay_minutes=5)
    assert exc_info.value.status_code == 404
