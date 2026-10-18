def test_login_success_returns_token(client):
    r = client.post("/auth/login", data={"username": "admin", "password": "admin123"})
    assert r.status_code == 200 and r.json()["token_type"] == "bearer"


def test_login_wrong_password_rejected(client):
    assert client.post("/auth/login", data={"username": "admin", "password": "nope"}).status_code == 401


def test_login_unknown_user_rejected(client):
    assert client.post("/auth/login", data={"username": "ghost", "password": "x"}).status_code == 401


def test_protected_route_requires_token(client):
    assert client.get("/stations").status_code == 401


def test_garbage_token_rejected(client):
    assert client.get("/stations", headers={"Authorization": "Bearer abc.def.ghi"}).status_code == 401


def test_profile_returns_role(client, admin, operator):
    assert client.get("/auth/me", headers=admin).json()["role"] == "admin"
    me = client.get("/auth/me", headers=operator).json()
    assert me["role"] == "operator" and me["assigned_station"] == "Taipei Main Station"


def test_admin_route_blocks_operator(client, admin, operator):
    assert client.get("/admin/ping", headers=admin).status_code == 200
    assert client.get("/admin/ping", headers=operator).status_code == 403
