def test_login_success(client, admin_user):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "admin@test.io", "password": "TestPassword123!"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "admin@test.io"
    assert data["user"]["role"] == "ADMIN"
    assert "password_hash" not in data["user"]


def test_login_invalid_password(client, admin_user):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "admin@test.io", "password": "WrongPassword!"}
    )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


def test_login_nonexistent_user(client):
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "nobody@test.io", "password": "SomePassword123!"}
    )
    assert response.status_code == 401


def test_get_current_user_me(client, admin_headers):
    response = client.get("/api/v1/auth/me", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "admin@test.io"
    assert data["role"] == "ADMIN"


def test_logout_endpoint(client, operator_headers):
    response = client.post("/api/v1/auth/logout", headers=operator_headers)
    assert response.status_code == 200
    assert "Successfully logged out" in response.json()["message"]
