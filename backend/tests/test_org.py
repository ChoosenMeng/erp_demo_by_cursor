"""Org API and permission/company-context tests."""

from fastapi.testclient import TestClient

from app.main import app
from app.modules.org.seed import ADMIN_PASSWORD, ADMIN_USERNAME

client = TestClient(app)


def _login() -> str:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
    )
    assert response.status_code == 200
    return response.json()["data"]["access_token"]


def test_refresh_token() -> None:
    """Refresh endpoint returns a new access token."""
    login = client.post(
        "/api/v1/auth/login",
        json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
    )
    refresh = login.json()["data"]["refresh_token"]
    response = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert response.status_code == 200
    assert response.json()["data"]["access_token"]


def test_me_company_header() -> None:
    """X-Company-Id is accepted when user belongs to the company."""
    token = _login()
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    company_id = me.json()["data"]["company_id"]
    assert company_id is not None

    response = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Company-Id": str(company_id),
        },
    )
    assert response.status_code == 200
    assert response.json()["data"]["company_id"] == company_id


def test_me_invalid_company_forbidden() -> None:
    """Unknown company id for user returns 403."""
    token = _login()
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}", "X-Company-Id": "999999"},
    )
    assert response.status_code == 403
    assert response.json()["code"] == 40300


def test_org_users_requires_auth() -> None:
    """Org endpoints require bearer token."""
    response = client.get("/api/v1/org/users")
    assert response.status_code == 401


def test_admin_can_list_users_and_roles() -> None:
    """Admin wildcard permission can access org APIs."""
    token = _login()
    headers = {"Authorization": f"Bearer {token}"}
    users = client.get("/api/v1/org/users", headers=headers)
    roles = client.get("/api/v1/org/roles", headers=headers)
    assert users.status_code == 200
    assert roles.status_code == 200
    assert users.json()["data"]["meta"]["total"] >= 1
