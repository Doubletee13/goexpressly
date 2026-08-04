"""
tests/test_auth.py — Auth endpoint tests.
"""


def test_login_success(client, seeded_admin):
    resp = client.post(
        "/api/auth/login",
        json={"email": "test@goexpressly.com", "password": "TestPass1!"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client, seeded_admin):
    resp = client.post(
        "/api/auth/login",
        json={"email": "test@goexpressly.com", "password": "WrongPassword"},
    )
    assert resp.status_code == 401


def test_login_unknown_email(client):
    resp = client.post(
        "/api/auth/login",
        json={"email": "nobody@example.com", "password": "WrongPassword"},
    )
    assert resp.status_code == 401


def test_me_authenticated(client, auth_headers):
    resp = client.get("/api/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "test@goexpressly.com"
    assert "hashed_password" not in data


def test_me_unauthenticated(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_me_invalid_token(client):
    resp = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid.token.here"})
    assert resp.status_code == 401
