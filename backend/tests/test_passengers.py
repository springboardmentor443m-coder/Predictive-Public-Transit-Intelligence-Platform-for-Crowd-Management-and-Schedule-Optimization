import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_get_live_passenger_stream():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/passengers/live-stream")
    assert response.status_code == 200
    data = response.json()
    assert "timestamp" in data
    assert "system_inflow_ppm" in data
    assert "system_outflow_ppm" in data
    assert "recent_tap_events" in data
    assert len(data["recent_tap_events"]) > 0
    assert "trains" in data
    assert len(data["trains"]) > 0
    first_train = data["trains"][0]
    assert "cars" in first_train
    assert len(first_train["cars"]) == 4
    assert "gtfs_rt_status" in data


@pytest.mark.asyncio
async def test_get_train_telemetry():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/passengers/train-telemetry")
    assert response.status_code == 200
    trains = response.json()
    assert isinstance(trains, list)
    assert len(trains) >= 4
    first_train = trains[0]
    assert "train_code" in first_train
    assert "overall_load_pct" in first_train
    assert "cars" in first_train


@pytest.mark.asyncio
async def test_get_station_metrics():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/passengers/station-metrics")
    assert response.status_code == 200
    metrics = response.json()
    assert isinstance(metrics, list)
    assert len(metrics) >= 16
    first_m = metrics[0]
    assert "tap_ins_last_minute" in first_m
    assert "tap_outs_last_minute" in first_m
    assert "net_flux" in first_m


@pytest.mark.asyncio
async def test_gtfs_rt_configuration():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Check current status
        status_resp = await ac.get("/api/v1/passengers/gtfs-rt-status")
        assert status_resp.status_code == 200
        
        # Configure test endpoint (disabled or fallback)
        config_payload = {
            "feed_url": "https://api.example.com/gtfs-rt/vehicle-positions",
            "provider_name": "Test Agency Feed",
            "is_enabled": False
        }
        resp = await ac.post("/api/v1/passengers/gtfs-rt-config", json=config_payload)
        assert resp.status_code == 200
        result = resp.json()
        assert result["is_active"] is False
