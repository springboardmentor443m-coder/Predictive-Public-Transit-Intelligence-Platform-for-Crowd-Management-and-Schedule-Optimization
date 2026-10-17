def test_admin_access_to_user_management(client, admin_headers):
    response = client.get("/api/v1/users", headers=admin_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_operator_denied_user_management(client, operator_headers):
    response = client.get("/api/v1/users", headers=operator_headers)
    assert response.status_code == 403
    assert "Access denied" in response.json()["detail"]


def test_unauthenticated_access_denied(client):
    response = client.get("/api/v1/users")
    assert response.status_code == 401


def test_operator_access_to_own_profile(client, operator_headers):
    response = client.get("/api/v1/profile", headers=operator_headers)
    assert response.status_code == 200
    assert response.json()["email"] == "operator@test.io"
