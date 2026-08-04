"""Auth API tests (requires seeded admin user in DB)."""

from fastapi.testclient import TestClient

from app.main import app
from app.modules.org.seed import ADMIN_PASSWORD, ADMIN_USERNAME

client = TestClient(app)


def test_login_success() -> None:
    """Admin can login with seed credentials."""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    data = body["data"]
    assert data["token_type"] == "bearer"
    assert data["access_token"]
    assert data["user"]["username"] == ADMIN_USERNAME
    assert "admin" in data["user"]["roles"]
    assert data["user"]["permissions"] == ["*"]


def test_login_bad_password() -> None:
    """Wrong password returns 401 business error."""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": ADMIN_USERNAME, "password": "wrong-pass"},
    )
    assert response.status_code == 401
    assert response.json()["code"] == 40100


def test_me_requires_token() -> None:
    """/me without token is unauthorized."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_me_with_token() -> None:
    """/me returns profile when access token is valid."""
    login = client.post(
        "/api/v1/auth/login",
        json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
    )
    token = login.json()["data"]["access_token"]
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["username"] == ADMIN_USERNAME
    assert data["company_id"] is not None
