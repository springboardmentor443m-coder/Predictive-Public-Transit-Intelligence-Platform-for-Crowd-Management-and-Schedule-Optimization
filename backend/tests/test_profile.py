def test_update_profile(client, operator_headers):
    response = client.put(
        "/api/v1/profile",
        json={"name": "Updated Operator Name"},
        headers=operator_headers
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Operator Name"


def test_change_password_success(client, operator_user, operator_headers):
    response = client.post(
        "/api/v1/profile/change-password",
        json={"current_password": "TestPassword123!", "new_password": "NewSecretPassword123!"},
        headers=operator_headers
    )
    assert response.status_code == 200
    assert "Password changed successfully" in response.json()["message"]

    # Re-login with new password
    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": "operator@test.io", "password": "NewSecretPassword123!"}
    )
    assert login_res.status_code == 200


def test_change_password_invalid_current(client, operator_headers):
    response = client.post(
        "/api/v1/profile/change-password",
        json={"current_password": "WrongCurrentPassword!", "new_password": "NewSecretPassword123!"},
        headers=operator_headers
    )
    assert response.status_code == 400
    assert "Incorrect current password" in response.json()["detail"]
