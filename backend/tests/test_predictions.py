import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_get_station_forecast():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/predictions/forecast/1?horizon=30")
    assert response.status_code == 200
    data = response.json()
    assert data["station_id"] == 1
    assert "forecast_points" in data
    assert len(data["forecast_points"]) > 0
    assert "confidence_interval_upper" in data["forecast_points"][0]


@pytest.mark.asyncio
async def test_get_anomalies():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/predictions/anomalies")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
