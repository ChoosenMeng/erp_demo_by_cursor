"""M5 demo seed and multi-company isolation smoke."""

from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.main import app
from app.modules.demo.seed import run_demo_seed
from app.modules.org.seed import ADMIN_PASSWORD, ADMIN_USERNAME, run_seed

client = TestClient(app)


def test_second_company_master_isolation() -> None:
    """DEFAULT and SECOND companies keep separate master rows."""
    db = SessionLocal()
    try:
        run_seed(db)
        demo = run_demo_seed(db, with_second_company=True)
        assert demo["second_company_id"] is not None
        default_id = demo["company_id"]
        second_id = demo["second_company_id"]
    finally:
        db.close()

    login = client.post(
        "/api/v1/auth/login",
        json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
    )
    assert login.status_code == 200
    token = login.json()["data"]["access_token"]

    default_mats = client.get(
        "/api/v1/master/materials",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Company-Id": str(default_id),
        },
    )
    second_mats = client.get(
        "/api/v1/master/materials",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Company-Id": str(second_id),
        },
    )
    assert default_mats.status_code == 200
    assert second_mats.status_code == 200
    default_ids = {i["id"] for i in default_mats.json()["data"]["items"]}
    second_ids = {i["id"] for i in second_mats.json()["data"]["items"]}
    assert default_ids.isdisjoint(second_ids)
    assert any(i["code"] == "FG-001" for i in default_mats.json()["data"]["items"])
    assert any(i["code"] == "FG-001" for i in second_mats.json()["data"]["items"])
