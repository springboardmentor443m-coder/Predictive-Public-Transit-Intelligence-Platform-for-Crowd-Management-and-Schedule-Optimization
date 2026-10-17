def test_audit_logs_retrieval(client, admin_headers):
    # Perform a login to generate an audit log entry
    client.post(
        "/api/v1/auth/login",
        data={"username": "admin@test.io", "password": "TestPassword123!"}
    )

    response = client.get("/api/v1/audit-logs", headers=admin_headers)
    assert response.status_code == 200
    logs = response.json()
    assert isinstance(logs, list)
    assert len(logs) > 0
    assert any(log["action"] == "LOGIN_SUCCESS" for log in logs)


def test_operator_access_audit_logs_forbidden(client, operator_headers):
    response = client.get("/api/v1/audit-logs", headers=operator_headers)
    assert response.status_code == 403
