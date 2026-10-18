import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_get_stations_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/stations")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 80
    codes = [s["station_code"] for s in data]
    assert "KGWA" in codes or "BYPH" in codes or "WHTM" in codes


@pytest.mark.asyncio
async def test_get_routes_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/routes")
    assert res.status_code == 200
    data = res.json()
    assert "routes" in data
    route_names = [r["route_name"] for r in data["routes"]]
    assert "Purple Line" in route_names
    assert "Green Line" in route_names


@pytest.mark.asyncio
async def test_get_schedule_station_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/schedule/1")
    assert res.status_code == 200
    data = res.json()
    assert "station_id" in data
    assert data["data_mode"] == "SCHEDULED_TIMETABLE_ONLY"
    assert "upcoming_departures" in data


@pytest.mark.asyncio
async def test_get_crowd_stations_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/crowd/stations")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 80


@pytest.mark.asyncio
async def test_get_alerts_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/alerts")
    assert res.status_code in (200, 307)


@pytest.mark.asyncio
async def test_predict_demand_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/predict/demand", json={"station_id": 1, "horizon_hours": 1})
    assert res.status_code == 200
    data = res.json()
    assert "predicted_inflow_rate" in data
    assert "model_architecture" in data
    assert "XGBoost" in data["model_architecture"]


@pytest.mark.asyncio
async def test_get_anomalies_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/anomalies")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_data_sources_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/data/sources")
    assert res.status_code == 200
    data = res.json()
    assert "sources" in data
    source_names = [s["source"] for s in data["sources"]]
    assert "BMRCL GTFS" in source_names
    assert "BMRCL RIDERSHIP" in source_names
    assert "LIVE PASSENGER FEED" in source_names
    assert "LIVE GPS" in source_names
