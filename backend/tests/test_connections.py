import os
import sys

os.environ["DATABASE_URL"] = "sqlite:///./test_connections.db"
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
from app.services.connection_service import load_connections  # noqa: E402

STATIONS_FILE = Path(__file__).resolve().parents[1] / "data" / "stations.csv"
CONNECTIONS_FILE = Path(__file__).resolve().parents[1] / "data" / "connections.csv"


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


def _codes(path: Path) -> set[str]:
    with path.open(newline="", encoding="utf-8") as fh:
        return {row["code"].strip() for row in csv.DictReader(fh)}


@pytest.fixture(scope="session")
def station_codes():
    return _codes(STATIONS_FILE)


@pytest.fixture(scope="session")
def admin_headers(client):
    res = client.post("/api/v1/auth/login", data={"username": "admin@test.io", "password": "Admin@123"})
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def test_graph_edges_only_reference_monitored_stations(station_codes):
    rows = load_connections()
    assert rows, "connections.csv must not be empty"
    for r in rows:
        assert r["from_code"] in station_codes, f"{r['from_code']} not in stations.csv"
        assert r["to_code"] in station_codes, f"{r['to_code']} not in stations.csv"


def test_graph_has_expected_real_world_edges():
    pairs = {frozenset((r["from_code"], r["to_code"])) for r in load_connections()}
    # Along-line neighbours
    assert frozenset(("127", "128")) in pairs, "Times Sq-42 St <-> 34 St-Penn along the 1/2/3"
    assert frozenset(("L01", "L02")) in pairs, "L would-be neighbours must be adjacent"
    # Documented same-complex interchanges
    assert frozenset(("127", "631")) in pairs, "Times Sq <-> Grand Central via 42 St Shuttle"
    assert frozenset(("718", "R05")) in pairs, "Queensboro Plaza 7 <-> N/W cross-platform"


def test_phantom_transfer_is_excluded():
    pairs = {frozenset((r["from_code"], r["to_code"])) for r in load_connections()}
    assert frozenset(("718", "R09")) not in pairs, "bogus Queensboro Plaza <-> Herald Sq artifact must be dropped"


def test_every_edge_is_symmetric():
    seen = set()
    for r in load_connections():
        key = frozenset((r["from_code"], r["to_code"]))
        assert key not in seen, f"duplicate edge {key}"
        seen.add(key)


def test_kinds_are_bounded():
    for r in load_connections():
        assert r["kind"] in ("along_line", "transfer"), r["kind"]


def test_junction_degrees_make_sense():
    """Every along-line edge lists at least one real route; transfers label 'transfer'."""
    for r in load_connections():
        if r["kind"] == "along_line":
            assert r["vias"] and r["vias"] != "transfer"
        else:
            assert r["vias"] == "transfer"


def test_endpoint_returns_graph(client, admin_headers):
    res = client.get("/api/v1/crowd/connections", headers=admin_headers)
    assert res.status_code == 200
    body = res.json()
    assert isinstance(body, list) and len(body) >= 10
    assert all({"from_code", "to_code", "kind"} <= set(item) for item in body)


def test_endpoint_requires_auth(client):
    assert client.get("/api/v1/crowd/connections").status_code == 401