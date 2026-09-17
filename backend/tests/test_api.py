import os
import sys
from pathlib import Path
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Use SQLite and fast predictor for instantaneous testing
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SKIP_HEAVY_MODEL_LOAD"] = "true"

from app.db.base import Base
from app.database import get_db
from app.models.station import Station
from app.models.alert import Alert
from app.models.user import User
from app.core.security import get_password_hash
from app.main import app

# In-memory SQLite for instantaneous testing
TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

Base.metadata.create_all(bind=test_engine)

# Seed minimal test data
with TestingSessionLocal() as session:
    # Users
    session.add(User(username="admin", hashed_password=get_password_hash("adminpassword"), role="admin"))
    session.add(User(username="operator", hashed_password=get_password_hash("operatorpassword"), role="operator"))
    
    # Stations
    session.add(Station(
        station_code="222",
        name_en="Gangnam",
        name_kr="강남",
        line="Line 2",
        latitude=37.497952,
        longitude=127.027619,
        district="Gangnam-gu"
    ))
    session.add(Station(
        station_code="150",
        name_en="Seoul Station",
        name_kr="서울역",
        line="Line 1",
        latitude=37.554648,
        longitude=126.972559,
        district="Jung-gu"
    ))
    
    # Alerts
    session.add(Alert(
        id=1,
        station_code="222",
        alert_type="overcrowding",
        severity="critical",
        message="Platform density high at Gangnam",
        created_at=datetime.now(timezone.utc),
        resolved=False
    ))
    session.commit()


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "MetroFlow"


def test_list_stations():
    response = client.get("/api/v1/stations")
    assert response.status_code == 200
    stations = response.json()
    assert len(stations) >= 2
    assert any(s["station_code"] == "222" for s in stations)


def test_search_stations():
    # Search by English name
    res_en = client.get("/api/v1/stations?search=Gangnam")
    assert res_en.status_code == 200
    assert len(res_en.json()) == 1
    assert res_en.json()[0]["station_code"] == "222"

    # Filter by line
    res_line = client.get("/api/v1/stations?line=Line 2")
    assert res_line.status_code == 200
    assert all(s["line"] == "Line 2" for s in res_line.json())


def test_get_station_detail():
    response = client.get("/api/v1/stations/222")
    assert response.status_code == 200
    data = response.json()
    assert data["station_code"] == "222"
    assert data["name_en"] == "Gangnam"

    # 404 test
    res_404 = client.get("/api/v1/stations/invalid_99999")
    assert res_404.status_code == 404
    assert "not found" in res_404.json()["detail"].lower()


def test_predict_crowd():
    now_iso = datetime.now(timezone.utc).isoformat()
    
    # Valid prediction
    response = client.post(
        "/api/v1/predict/crowd",
        json={"station_code": "222", "timestamp": now_iso}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["station_code"] == "222"
    assert "predicted_density" in data
    assert data["congestion_label"] in ["low", "medium", "high", "critical"]

    # 404 non-existent station
    res_404 = client.post(
        "/api/v1/predict/crowd",
        json={"station_code": "non_existent_99", "timestamp": now_iso}
    )
    assert res_404.status_code == 404

    # 422 unparseable timestamp
    res_422 = client.post(
        "/api/v1/predict/crowd",
        json={"station_code": "222", "timestamp": "invalid-timestamp-string"}
    )
    assert res_422.status_code == 422


def test_schedule_recommendation():
    response = client.get("/api/v1/schedule/recommend/222")
    assert response.status_code == 200
    data = response.json()
    assert data["station_code"] == "222"
    assert "current_density" in data
    assert "recommended_action" in data
    assert "urgency" in data
    assert "reason" in data
    assert "calculated_at" in data


def test_post_delay_propagation():
    # Valid delay report
    response = client.post(
        "/api/v1/schedule/delay",
        json={
            "line": "Line 2",
            "station_code": "222",
            "delay_minutes": 8
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["line"] == "Line 2"
    assert data["incident_station_code"] == "222"
    assert data["initial_delay_minutes"] == 8
    assert "affected_stations" in data

    # 404 for invalid line / station mismatch
    res_404 = client.post(
        "/api/v1/schedule/delay",
        json={
            "line": "Line 9",
            "station_code": "222",  # Gangnam is on Line 2
            "delay_minutes": 5
        }
    )
    assert res_404.status_code == 404


def test_alerts_listing_and_filtering():
    response = client.get("/api/v1/alerts")
    assert response.status_code == 200
    alerts = response.json()
    assert len(alerts) >= 1

    # Filter unresolved alerts
    res_unresolved = client.get("/api/v1/alerts?resolved=false")
    assert res_unresolved.status_code == 200
    assert all(a["resolved"] is False for a in res_unresolved.json())


def test_auth_and_resolve_alert():
    # 1. Login with admin credentials
    login_res = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "adminpassword"}
    )
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data
    token = token_data["access_token"]

    # 2. Try resolving without token -> 401 Unauthorized
    res_unauth = client.post("/api/v1/alerts/resolve/1")
    assert res_unauth.status_code == 401

    # 3. Resolve with valid Bearer token -> 200 OK
    headers = {"Authorization": f"Bearer {token}"}
    res_resolve = client.post("/api/v1/alerts/resolve/1", headers=headers)
    assert res_resolve.status_code == 200
    assert res_resolve.json()["resolved"] is True

    # 4. Resolve non-existent alert -> 404 Not Found
    res_404 = client.post("/api/v1/alerts/resolve/999999", headers=headers)
    assert res_404.status_code == 404


def test_invalid_login():
    res = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "wrongpassword"}
    )
    assert res.status_code == 401
    assert "Invalid username or password" in res.json()["detail"]
