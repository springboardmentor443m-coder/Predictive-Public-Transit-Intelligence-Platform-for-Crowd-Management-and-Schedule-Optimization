import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_get_active_schedules():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/schedules/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2


@pytest.mark.asyncio
async def test_schedule_override_safety_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Invalid headway < 3 mins
        response = await ac.post(
            "/api/v1/schedules/override",
            json={
                "schedule_id": 101,
                "new_headway_minutes": 1,
                "reason": "Test safety violation"
            }
        )
    assert response.status_code == 200
    data = response.json()
    assert data["applied"] is False
    assert data["conflict_detected"] is True
