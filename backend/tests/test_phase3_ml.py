import pytest


def test_get_network_summary(client, admin_headers):
    response = client.get("/api/v1/ml/network-summary", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total_nodes"] == 12
    assert data["total_edges"] == 14
    assert data["network_model_accuracy"] is None


def test_get_delay_impact(client, admin_headers):
    response = client.get("/api/v1/ml/delay-impact", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "route_id" in data[0]
    assert "severity_tier" in data[0]


def test_get_network_risk(client, admin_headers):
    response = client.get("/api/v1/ml/network-risk", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Network risk may be empty if network_congestion_predictions.csv is absent
    if len(data) > 0:
        assert "network_risk" in data[0]
        assert "contributing_factors" in data[0]


def test_get_station_connections(client, admin_headers):
    response = client.get("/api/v1/ml/station/164/connections", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["station_complex_id"] == "164"
    assert "degree" in data
    assert len(data["neighbors"]) > 0


def test_get_scheduling_intelligence(client, admin_headers):
    response = client.get("/api/v1/ml/scheduling-intelligence", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "recommended_headway_minutes" in data[0]
    assert "advisory_disclaimer" in data[0]
    assert "OPERATOR ADVISORY" in data[0]["advisory_disclaimer"]


def test_get_traffic_analytics(client, admin_headers):
    response = client.get("/api/v1/ml/analytics/traffic", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert "hourly_patterns" in data
    assert len(data["hourly_patterns"]) == 24
    assert "weekday_patterns" in data
    assert "top_stations" in data
    assert "peak_summary" in data
