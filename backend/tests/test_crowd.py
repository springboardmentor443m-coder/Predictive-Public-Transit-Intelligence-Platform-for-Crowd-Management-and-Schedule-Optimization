import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_get_station_densities():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/crowd/densities")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 15
    first_st = data[0]
    assert "density_percentage" in first_st
    assert "status" in first_st
    assert first_st["status"] in ["NORMAL", "MODERATE", "CRITICAL"]


@pytest.mark.asyncio
async def test_get_crowd_summary():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/crowd/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_system_occupancy" in data
    assert "average_density_percentage" in data
    assert "critical_stations_count" in data
