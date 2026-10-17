def test_admin_create_user(client, admin_headers):
    response = client.post(
        "/api/v1/users",
        json={
            "email": "new_operator@test.io",
            "name": "New Operator",
            "password": "NewOperatorPassword123!",
            "role": "OPERATOR",
            "is_active": True
        },
        headers=admin_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "new_operator@test.io"
    assert data["role"] == "OPERATOR"
    assert "password_hash" not in data


def test_admin_update_user_role(client, admin_headers, operator_user):
    response = client.patch(
        f"/api/v1/users/{operator_user.id}/role",
        json={"role": "ADMIN"},
        headers=admin_headers
    )
    assert response.status_code == 200
    assert response.json()["role"] == "ADMIN"


def test_admin_toggle_user_status(client, admin_headers, operator_user):
    response = client.patch(
        f"/api/v1/users/{operator_user.id}/status",
        json={"is_active": False},
        headers=admin_headers
    )
    assert response.status_code == 200
    assert response.json()["is_active"] is False
