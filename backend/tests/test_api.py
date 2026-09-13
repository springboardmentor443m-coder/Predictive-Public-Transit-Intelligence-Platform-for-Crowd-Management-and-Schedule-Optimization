import os
import sys

os.environ["DATABASE_URL"] = "sqlite:///./test_metroflow.db"
os.environ["MONGODB_URL"] = ""
os.environ["REDIS_URL"] = ""
os.environ["METROFLOW_ENABLE_REALTIME"] = ""

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.models import alert, ridership, schedule, station, train, user  # noqa: E402,F401
from app.main import app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def seed_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    db.add_all([
        user.User(id="usr_admin", email="admin@test.io", full_name="Admin", hashed_password=hash_password("Admin@123"), role="admin"),
        user.User(id="usr_op", email="op@test.io", full_name="Operator", hashed_password=hash_password("Operator@123"), role="operator"),
        user.User(id="usr_view", email="view@test.io", full_name="Viewer", hashed_password=hash_password("Viewer@123"), role="viewer"),
    ])
    db.add(station.Station(id="ST01", code="ST01", name="Central", line="Red", zone="Z1", capacity_per_hour=500))
    db.add(station.Station(id="ST02", code="ST02", name="Riverside", line="Red", zone="Z1", capacity_per_hour=430))
    db.add(train.Train(id="TR-R01", code="TR-R01", model="M8", capacity=1000, status="active"))
    from datetime import datetime, timedelta

    now = datetime.utcnow()
    db.add(schedule.TrainSchedule(
        id="SCH-T1", train_id="TR-R01", station_id="ST01", direction="northbound",
        arrival=now + timedelta(hours=1), departure=now + timedelta(hours=1, minutes=1),
        headway_min=6, status="on_time", delay_min=0, is_peak="no",
    ))
    for h in range(24):
        db.add(ridership.RidershipRecord(
            id=f"RR-{h}", station_id="ST01",
            timestamp=now - timedelta(hours=24 - h),
            entries=200 + h * 10, exits=180 + h * 10, occupancy=150 + h * 12,
            congestion_level="low" if h < 12 else "medium",
        ))
        db.add(ridership.RidershipRecord(
            id=f"RR2-{h}", station_id="ST02",
            timestamp=now - timedelta(hours=24 - h),
            entries=90 + h * 5, exits=80 + h * 5, occupancy=70 + h * 6,
            congestion_level="low",
        ))
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


def _login(client, email, password):
    res = client.post("/api/v1/auth/login", data={"username": email, "password": password})
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


@pytest.fixture(scope="session")
def admin_headers(client):
    return _login(client, "admin@test.io", "Admin@123")


@pytest.fixture(scope="session")
def viewer_headers(client):
    return _login(client, "view@test.io", "Viewer@123")


# ---------- Auth & User Management ----------

def test_health(client):
    assert client.get("/api/v1/health").json()["status"] == "ok"


def test_login_rejects_bad_password(client):
    res = client.post("/api/v1/auth/login", data={"username": "admin@test.io", "password": "wrong"})
    assert res.status_code == 401


def test_me_requires_token(client):
    assert client.get("/api/v1/auth/me").status_code == 401


def test_me_returns_profile(client, admin_headers):
    me = client.get("/api/v1/auth/me", headers=admin_headers).json()
    assert me["email"] == "admin@test.io"
    assert me["role"] == "admin"


def test_deactivated_user_cannot_login(client, admin_headers):
    created = client.post(
        "/api/v1/users/", headers=admin_headers,
        json={"email": "temp@metroflow.io", "full_name": "Temp User", "role": "viewer", "password": "Secret@123"},
    )
    assert created.status_code == 200
    uid = created.json()["id"]

    assert client.post(f"/api/v1/users/{uid}/deactivate", headers=admin_headers).status_code == 200

    res = client.post("/api/v1/auth/login", data={"username": "temp@metroflow.io", "password": "Secret@123"})
    assert res.status_code == 403
    assert "deactivated" in res.json()["detail"].lower()

    # Wrong password on an existing account stays a 401 with the standard detail.
    res = client.post("/api/v1/auth/login", data={"username": "admin@test.io", "password": "nope"})
    assert res.status_code == 401


def test_admin_lists_users(client, admin_headers):
    users = client.get("/api/v1/users/", headers=admin_headers).json()
    assert len(users) == 4


def test_viewer_cannot_list_users(client, viewer_headers):
    assert client.get("/api/v1/users/", headers=viewer_headers).status_code == 403


def test_register_forces_viewer_role(client):
    res = client.post(
        "/api/v1/auth/register",
        json={"email": "selfreg@metroflow.io", "full_name": "Self Reg", "password": "SelfReg@123", "role": "admin"},
    )
    assert res.status_code == 200
    assert res.json()["role"] == "viewer"


def test_register_rejects_duplicate_email(client):
    res = client.post(
        "/api/v1/auth/register",
        json={"email": "selfreg@metroflow.io", "full_name": "Dup", "password": "SelfReg@123"},
    )
    assert res.status_code == 400


def test_user_updates_own_profile_via_users_me(client, viewer_headers):
    res = client.put("/api/v1/users/me", headers=viewer_headers, json={"full_name": "Jordan Lee II"})
    assert res.status_code == 200
    assert res.json()["full_name"] == "Jordan Lee II"


def test_users_me_ignores_role_escalation(client, viewer_headers):
    res = client.put(
        "/api/v1/users/me", headers=viewer_headers,
        json={"full_name": "Jordan Lee III", "role": "admin", "email": "hax@metroflow.io"},
    )
    assert res.status_code == 200
    assert res.json()["role"] == "viewer"
    assert res.json()["email"] == "view@test.io"


def test_users_me_requires_auth(client):
    assert client.put("/api/v1/users/me", json={"full_name": "x"}).status_code == 401


def test_admin_partial_update_preserves_password(client, admin_headers):
    created = client.post(
        "/api/v1/users/", headers=admin_headers,
        json={"email": "partial@metroflow.io", "full_name": "Partial User", "role": "operator", "password": "KeepMe@123"},
    )
    assert created.status_code == 200
    uid = created.json()["id"]

    renamed = client.put(f"/api/v1/users/{uid}", headers=admin_headers, json={"full_name": "Renamed User"})
    assert renamed.status_code == 200
    assert renamed.json()["full_name"] == "Renamed User"
    assert renamed.json()["role"] == "operator"

    # A partial update must not reset the password.
    login = client.post("/api/v1/auth/login", data={"username": "partial@metroflow.io", "password": "KeepMe@123"})
    assert login.status_code == 200


def test_users_me_password_change(client, admin_headers):
    login = client.post("/api/v1/auth/login", data={"username": "partial@metroflow.io", "password": "KeepMe@123"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    changed = client.put("/api/v1/users/me", headers=headers, json={"password": "NewPass@123"})
    assert changed.status_code == 200
    assert client.post(
        "/api/v1/auth/login", data={"username": "partial@metroflow.io", "password": "NewPass@123"}
    ).status_code == 200


def test_non_admin_cannot_update_other_users(client, viewer_headers):
    assert client.put(
        "/api/v1/users/usr_admin", headers=viewer_headers, json={"full_name": "Hacker"}
    ).status_code == 403


# ---------- Crowd Monitoring ----------

def test_live_crowd(client, viewer_headers):
    live = client.get("/api/v1/crowd/live", headers=viewer_headers).json()
    assert {s["station_id"] for s in live} == {"ST01", "ST02"}
    assert all(0 <= s["occupancy_pct"] <= 100 for s in live)


def test_heatmap(client, viewer_headers):
    hm = client.get("/api/v1/crowd/heatmap", headers=viewer_headers).json()
    assert {p["station_id"] for p in hm} == {"ST01", "ST02"}
    assert all("occupancy_pct" in p for p in hm)


def test_station_history(client, viewer_headers):
    hist = client.get("/api/v1/crowd/station/ST01/history?hours=24", headers=viewer_headers).json()
    assert len(hist) >= 20


# ---------- AI Predictions ----------

def test_crowd_prediction(client, viewer_headers):
    pred = client.get("/api/v1/predictions/crowd?hours=6", headers=viewer_headers).json()
    assert len(pred) == 6
    assert all("predicted_occupancy_pct" in p and "congestion_level" in p for p in pred)


def test_demand_forecast(client, viewer_headers):
    dem = client.get("/api/v1/predictions/demand?hours=6", headers=viewer_headers).json()
    assert len(dem) == 6
    assert all(d["predicted_entries"] >= 0 for d in dem)


def test_recommendations(client, viewer_headers):
    recs = client.get("/api/v1/predictions/recommendations", headers=viewer_headers).json()
    assert len(recs) >= 1
    assert all("station_id" in r and "recommended_headway_min" in r for r in recs)


def test_traffic_patterns(client, viewer_headers):
    pat = client.get("/api/v1/predictions/patterns", headers=viewer_headers).json()
    assert len(pat) == 2
    p = pat[0]
    assert 0 <= p["peak_hour"] <= 23
    assert len(p["profile_24h"]) == 24


def test_predictions_differ_per_station(client, viewer_headers):
    a = client.get("/api/v1/predictions/crowd?station_id=ST01&hours=6", headers=viewer_headers).json()
    b = client.get("/api/v1/predictions/crowd?station_id=ST02&hours=6", headers=viewer_headers).json()
    assert [p["predicted_occupancy_pct"] for p in a] != [p["predicted_occupancy_pct"] for p in b]

    da = client.get("/api/v1/predictions/demand?station_id=ST01&hours=6", headers=viewer_headers).json()
    db_ = client.get("/api/v1/predictions/demand?station_id=ST02&hours=6", headers=viewer_headers).json()
    assert [p["predicted_entries"] for p in da] != [p["predicted_entries"] for p in db_]


# ---------- Scheduling ----------

def test_viewer_can_view_schedules_and_recommendations(client, viewer_headers):
    assert client.get("/api/v1/scheduling/schedules", headers=viewer_headers).status_code == 200
    assert client.get("/api/v1/scheduling/optimization", headers=viewer_headers).status_code == 200


def test_viewer_cannot_modify_schedules(client, viewer_headers):
    assert client.post(
        "/api/v1/scheduling/schedules", headers=viewer_headers,
        json={"id": "X", "train_id": "TR-R01", "station_id": "ST01", "direction": "northbound",
              "arrival": "2026-09-01T10:00:00", "departure": "2026-09-01T10:01:00"},
    ).status_code == 403
    assert client.post("/api/v1/scheduling/delay/SCH-T1", headers=viewer_headers, json={"delay_min": 5}).status_code == 403
    assert client.post("/api/v1/scheduling/apply-headway/ST01", headers=viewer_headers, json={}).status_code == 403


def test_schedule_crud_flow(client, admin_headers):
    created = client.post(
        "/api/v1/scheduling/schedules",
        headers=admin_headers,
        json={
            "id": "SCH-CRUD1", "train_id": "TR-R01", "station_id": "ST01",
            "direction": "southbound", "arrival": "2026-09-01T10:00:00",
            "departure": "2026-09-01T10:01:00", "headway_min": 8,
        },
    )
    assert created.status_code == 200, created.text

    updated = client.put(
        "/api/v1/scheduling/schedules/SCH-CRUD1",
        headers=admin_headers,
        json={
            "id": "SCH-CRUD1", "train_id": "TR-R01", "station_id": "ST01",
            "direction": "southbound", "arrival": "2026-09-01T11:00:00",
            "departure": "2026-09-01T11:01:00", "headway_min": 4,
        },
    )
    assert updated.status_code == 200
    assert updated.json()["headway_min"] == 4

    deleted = client.delete("/api/v1/scheduling/schedules/SCH-CRUD1", headers=admin_headers)
    assert deleted.status_code == 200


def test_delay_creates_notification_alert(client, admin_headers):
    res = client.post("/api/v1/scheduling/delay/SCH-T1", headers=admin_headers, json={"delay_min": 7})
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "delayed"
    assert body["alert_id"] is not None

    alerts = client.get("/api/v1/alerts/", headers=admin_headers).json()
    assert any(a["id"] == body["alert_id"] and a["type"] == "delay" for a in alerts)


def test_apply_headway_frequency_adjustment(client, admin_headers):
    res = client.post("/api/v1/scheduling/apply-headway/ST01", headers=admin_headers, json={})
    assert res.status_code == 200
    body = res.json()
    assert body["source"] == "ai_recommendation"
    assert body["schedules_updated"] >= 1


# ---------- Alerts ----------

def test_broadcast_admin_only(client, viewer_headers, admin_headers):
    assert client.post(
        "/api/v1/alerts/broadcast", headers=viewer_headers,
        json={"title": "x", "message": "y"},
    ).status_code == 403

    bc = client.post(
        "/api/v1/alerts/broadcast", headers=admin_headers,
        json={"type": "emergency", "severity": "high", "title": "Drill", "message": "Evacuation drill"},
    )
    assert bc.status_code == 200
    alert_id = bc.json()["id"]

    ack = client.post(f"/api/v1/alerts/{alert_id}/acknowledge", headers=admin_headers)
    assert ack.status_code == 200
    assert ack.json()["is_acknowledged"] is True


# ---------- Analytics ----------

def test_analytics_overview(client, viewer_headers):
    ov = client.get("/api/v1/analytics/overview", headers=viewer_headers).json()
    assert ov["total_stations"] == 2
    assert ov["total_trains"] == 1
    assert 0 <= ov["on_time_pct"] <= 100


def test_station_performance(client, viewer_headers):
    perf = client.get("/api/v1/analytics/station-performance", headers=viewer_headers).json()
    assert {row["station_id"] for row in perf} == {"ST01", "ST02"}
    assert all(0 <= row["punctuality_pct"] <= 100 for row in perf)


def test_traffic_series(client, viewer_headers):
    tr = client.get("/api/v1/analytics/traffic?hours=12", headers=viewer_headers).json()
    assert len(tr) == 12


# ---------- Resilience (graceful degradation, no raw 500s) ----------

def test_db_down_returns_clean_503(client, monkeypatch):
    from sqlalchemy.exc import OperationalError

    from app.core import database as core_database

    def _db_down():
        raise OperationalError("select 1", None, Exception("connection refused"))

    monkeypatch.setattr(core_database, "SessionLocal", _db_down)
    res = client.post("/api/v1/auth/login", data={"username": "admin@test.io", "password": "Admin@123"})
    assert res.status_code == 503
    assert "temporarily unavailable" in res.json()["detail"].lower()


def test_model_endpoint_also_clean_503_when_db_down(client, viewer_headers, monkeypatch):
    from sqlalchemy.exc import OperationalError

    from app.core import database as core_database

    def _db_down():
        raise OperationalError("select 1", None, Exception("connection refused"))

    monkeypatch.setattr(core_database, "SessionLocal", _db_down)
    res = client.get("/api/v1/predictions/crowd?hours=3", headers=viewer_headers)
    assert res.status_code == 503
    assert "temporarily unavailable" in res.json()["detail"].lower()


def test_broadcast_backoff_exponential():
    from app.services.realtime import _broadcast_backoff, _should_log_failure

    assert _broadcast_backoff(0) == 5.0
    assert _broadcast_backoff(1) == 5.0
    assert _broadcast_backoff(2) == 10.0
    assert _broadcast_backoff(3) == 20.0
    assert _broadcast_backoff(4) == 40.0
    assert _broadcast_backoff(5) == 80.0
    assert _broadcast_backoff(6) == 120.0
    assert _broadcast_backoff(99) == 120.0
    # Failure logging is throttled to doubling thresholds, not every cycle.
    assert _should_log_failure(1) and _should_log_failure(2)
    assert not _should_log_failure(3)
    assert _should_log_failure(4)
    assert not _should_log_failure(5)
