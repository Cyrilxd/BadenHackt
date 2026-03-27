"""Tests for POST /api/login and the authentication guard."""


def test_health_check(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


# ---------------------------------------------------------------------------
# POST /api/login
# ---------------------------------------------------------------------------


def test_login_valid_credentials_returns_token(client, user):
    resp = client.post(
        "/api/login",
        data={"username": user.username, "password": "test123"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"
    assert body["user"]["username"] == user.username


def test_login_wrong_password_returns_401(client, user):
    resp = client.post(
        "/api/login",
        data={"username": user.username, "password": "falsch"},
    )
    assert resp.status_code == 401


def test_login_unknown_user_returns_401(client, db):
    resp = client.post(
        "/api/login",
        data={"username": "nobody", "password": "test123"},
    )
    assert resp.status_code == 401


def test_login_missing_fields_returns_422(client):
    resp = client.post("/api/login", data={})
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Auth guard on protected endpoints
# ---------------------------------------------------------------------------


def test_protected_endpoint_without_token_returns_401(client):
    resp = client.get("/api/rooms")
    assert resp.status_code == 401


def test_protected_endpoint_with_invalid_token_returns_401(client):
    resp = client.get(
        "/api/rooms",
        headers={"Authorization": "Bearer this.is.not.valid"},
    )
    assert resp.status_code == 401


def test_protected_endpoint_with_valid_token_succeeds(client, auth_headers):
    resp = client.get("/api/rooms", headers=auth_headers)
    assert resp.status_code == 200
