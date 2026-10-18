from tests.conftest import BUSY, DATE


def test_live_snapshot_structure(client, admin):
    r = client.get("/crowd/live", headers=admin, params={"on_date": DATE, "hour": 18})
    body = r.json()
    assert r.status_code == 200 and len(body["stations"]) == 30
    s = body["stations"][0]
    assert {"station", "entries", "exits", "capacity", "congestion_pct", "status"} <= set(s)
    pcts = [x["congestion_pct"] for x in body["stations"]]
    assert pcts == sorted(pcts, reverse=True)
    assert all(0 <= p <= 100 for p in pcts)


def test_congestion_uses_station_capacity(client, admin):
    r = client.get(f"/crowd/station/{BUSY}", headers=admin, params={"on_date": DATE, "hour": 18}).json()
    assert r["congestion_pct"] == round(min(100, r["entries"] / r["capacity"] * 100), 1)


def test_defaults_to_latest_date(client, admin):
    assert client.get("/crowd/live", headers=admin).json()["date"] == "2023-12-31"


def test_heatmap_dimensions(client, admin):
    h = client.get("/crowd/heatmap", headers=admin, params={"on_date": DATE}).json()
    assert len(h["stations"]) == 30 and len(h["hours"]) == 24
    assert all(len(row) == 24 for row in h["matrix"])


def test_station_analytics(client, admin):
    a = client.get(f"/crowd/analytics/{BUSY}", headers=admin).json()
    assert a["peak_hour"] in (8, 18) and a["avg_daily_entries"] > 0 and len(a["hourly_profile"]) == 24


def test_invalid_inputs_rejected(client, admin):
    assert client.get("/crowd/live", headers=admin, params={"on_date": "31-12-2023"}).status_code == 422
    assert client.get("/crowd/live", headers=admin, params={"on_date": DATE, "hour": 25}).status_code == 422
    assert client.get("/crowd/live", headers=admin, params={"on_date": "2030-01-01"}).status_code == 404
    assert client.get("/crowd/station/Atlantis", headers=admin).status_code == 404


def test_operator_sees_only_assigned_station(client, operator):
    assert client.get("/stations", headers=operator).json()["stations"] == [BUSY]
    live = client.get("/crowd/live", headers=operator, params={"on_date": DATE, "hour": 18}).json()
    assert [s["station"] for s in live["stations"]] == [BUSY]
    assert client.get(f"/crowd/station/{BUSY}", headers=operator, params={"on_date": DATE, "hour": 8}).status_code == 200
    assert client.get("/crowd/station/Ximen", headers=operator, params={"on_date": DATE, "hour": 8}).status_code == 403
    assert client.get("/schedule/Ximen", headers=operator, params={"on_date": DATE}).status_code == 403
