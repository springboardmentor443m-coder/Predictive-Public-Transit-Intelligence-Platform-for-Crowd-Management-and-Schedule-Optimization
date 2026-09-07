import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.datasets.pipeline import pipeline_engine


def test_dataset_pipeline_execution():
    stats = pipeline_engine.run_pipeline()
    assert "total_records" in stats
    assert stats["total_records"] > 0
    assert "NYC MTA" in stats["sources"]


@pytest.mark.asyncio
async def test_get_dataset_stats_api():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/datasets/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_records" in data
    assert data["total_records"] > 0
    assert data["master_file_exists"] is True


@pytest.mark.asyncio
async def test_dataset_retrain_api():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/datasets/retrain")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert "metrics" in data
