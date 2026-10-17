import pytest


def test_get_anomalies(client, admin_headers):
    response = client.get("/api/v1/ml/anomalies", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert "is_available" in data
    assert "status_message" in data
    assert "anomalies" in data
    assert isinstance(data["is_available"], bool)
    assert isinstance(data["anomalies"], list)
