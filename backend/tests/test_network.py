import os
import sys

os.environ["DATABASE_URL"] = "sqlite:///./test_network.db"
os.environ["MONGODB_URL"] = ""
os.environ["REDIS_URL"] = ""
os.environ["METROFLOW_ENABLE_REALTIME"] = ""

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import csv  # noqa: E402
from pathlib import Path  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.models import station, user  # noqa: E402,F401
from app.main import app  # noqa: E402
from app.services.network_service import load_network  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def seed_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    db.add(user.User(id="usr_admin", email="admin@test.io", full_name="Admin", hashed_password=hash_password("Admin@123"), role="admin"))
    db.add(station.Station(id="128", code="128", name="34 St-Penn Station", line="1/2/3", zone="Z1", capacity_per_hour=11000))
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def admin_headers(client):
    res = client.post("/api/v1/auth/login", data={"username": "admin@test.io", "password": "Admin@123"})
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def _monitored_codes() -> list[str]:
    stations_file = Path(__file__).resolve().parents[1] / "data" / "stations.csv"
    with stations_file.open(newline="", encoding="utf-8") as fh:
        return [row["code"].strip() for row in csv.DictReader(fh)]


def test_network_has_real_scale():
    net = load_network()
    assert len(net["stations"]) >= 400, "the full network must cover the whole subway"
    assert len(net["segments"]) >= 500


def test_every_segment_references_a_known_station():
    net = load_network()
    codes = {s["c"] for s in net["stations"]}
    for seg in net["segments"]:
        assert seg["a"] in codes, seg["a"]
        assert seg["b"] in codes, seg["b"]


def test_all_monitored_codes_are_in_the_network():
    net = load_network()
    codes = {s["c"] for s in net["stations"]}
    for code in net["monitored"]:
        assert code in codes, code


def test_monitored_matches_stations_csv():
    net = load_network()
    assert sorted(net["monitored"]) == sorted(_monitored_codes())


def test_both_directions_collapse_to_one_segment():
    net = load_network()
    pairs = {frozenset((s["a"], s["b"])) for s in net["segments"]}
    assert len(pairs) == len(net["segments"]), "segments must be undirected-deduplicated"


def test_segments_carry_route_labels():
    net = load_network()
    labeled = [s for s in net["segments"] if s["r"]]
    assert len(labeled) >= 400


def test_endpoint_returns_network(client, admin_headers):
    res = client.get("/api/v1/crowd/network", headers=admin_headers)
    assert res.status_code == 200
    body = res.json()
    assert len(body["stations"]) >= 400
    assert len(body["segments"]) >= 500
    assert len(body["monitored"]) == 59


def test_endpoint_requires_auth(client):
    assert client.get("/api/v1/crowd/network").status_code == 401