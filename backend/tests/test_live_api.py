def test_get_live_health(client, operator_headers):
    response = client.get("/api/v1/live/health", headers=operator_headers)
    assert response.status_code == 200
    data = response.json()
    assert "provider_name" in data
    assert "status" in data
    assert isinstance(data["is_live"], bool)


def test_get_live_vehicles(client, operator_headers):
    response = client.get("/api/v1/live/vehicles", headers=operator_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_live_trips(client, operator_headers):
    response = client.get("/api/v1/live/trips", headers=operator_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_live_alerts(client, operator_headers):
    response = client.get("/api/v1/live/alerts", headers=operator_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_trigger_live_sync(client, operator_headers):
    response = client.post("/api/v1/live/sync", headers=operator_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("success", "error")
