from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 0
    assert body["data"]["status"] in {"healthy", "degraded"}
    assert "database" in body["data"]


def test_root() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["code"] == 0
