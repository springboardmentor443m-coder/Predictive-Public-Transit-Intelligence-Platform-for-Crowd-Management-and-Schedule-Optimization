import pytest


def test_websocket_connection_and_test_event(client, admin_token):
    ws_url = f"/api/v1/ws/events?token={admin_token}"
    with client.websocket_connect(ws_url) as websocket:
        data = websocket.receive_json()
        assert data["event"] == "CONNECTION_ESTABLISHED"
        assert data["data_state"] == "LIVE"

        # Trigger test event via HTTP
        response = client.post(
            "/api/v1/ws/test-event",
            json={"event_type": "UNIT_TEST_PING", "message": "Testing WebSocket pipeline"}
        )
        assert response.status_code == 200
        assert response.json()["status"] == "broadcast_sent"

        broadcast_data = websocket.receive_json()
        assert broadcast_data["event"] == "UNIT_TEST_PING"
        assert broadcast_data["data_state"] == "DEV_INFRASTRUCTURE_TEST"
