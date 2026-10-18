import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import ai_prediction

DATE = "2023-12-29"        # a Friday inside the dataset
FUTURE_DATE = "2024-03-15"  # beyond the dataset: forecasts must still work
BUSY = "Taipei Main Station"


@pytest.fixture(scope="session", autouse=True)
def trained_models():
    """Make sure model artifacts exist (trains once, ~20 s, only if missing)."""
    ai_prediction.get_model_metadata()
    ai_prediction._models()


@pytest.fixture(scope="session")
def client():
    return TestClient(app)


def _login(client, username, password):
    r = client.post("/auth/login", data={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(scope="session")
def admin(client):
    return _login(client, "admin", "admin123")


@pytest.fixture(scope="session")
def operator(client):
    return _login(client, "operator1", "operator123")
