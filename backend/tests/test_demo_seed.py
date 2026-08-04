"""Demo seed and multi-company isolation smoke (USCO / EUCO)."""

from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.main import app
from app.modules.demo.seed import run_demo_seed
from app.modules.org.seed import ADMIN_PASSWORD, ADMIN_USERNAME, run_seed

client = TestClient(app)


def test_multi_company_master_isolation() -> None:
    """USCO and EUCO keep separate master rows with same business codes."""
    db = SessionLocal()
    try:
        org = run_seed(db)
        demo = run_demo_seed(db, with_second_company=True)
        assert "USCO" in org["companies"]
        assert "EUCO" in org["companies"]
        assert "DEFAULT" in org["inactive_companies"]
        assert demo["second_company_id"] is not None
        usco_id = demo["company_id"]
        euco_id = demo["second_company_id"]
        assert demo["material_counts"]["USCO"] >= 5
        assert demo["material_counts"]["EUCO"] >= 5
    finally:
        db.close()

    login = client.post(
        "/api/v1/auth/login",
        json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
    )
    assert login.status_code == 200
    token = login.json()["data"]["access_token"]
    companies = login.json()["data"]["user"]["companies"]
    # Active entities only in switcher
    assert len(companies) == 2
    assert {c["code"] for c in companies} == {"USCO", "EUCO"}
    assert all("base_currency_code" in c for c in companies)
    default_codes = [c["code"] for c in companies if c["is_default"]]
    assert default_codes == ["USCO"]
    assert login.json()["data"]["user"]["company_id"] == usco_id

    usco_mats = client.get(
        "/api/v1/master/materials",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Company-Id": str(usco_id),
        },
    )
    euco_mats = client.get(
        "/api/v1/master/materials",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Company-Id": str(euco_id),
        },
    )
    assert usco_mats.status_code == 200
    assert euco_mats.status_code == 200
    usco_ids = {i["id"] for i in usco_mats.json()["data"]["items"]}
    euco_ids = {i["id"] for i in euco_mats.json()["data"]["items"]}
    assert usco_ids.isdisjoint(euco_ids)
    assert len(usco_ids) >= 5
    assert len(euco_ids) >= 5
    assert any(i["code"] == "FG-001" for i in usco_mats.json()["data"]["items"])
    assert any(i["code"] == "FG-001" for i in euco_mats.json()["data"]["items"])


def test_demo_users_login_and_currency_list() -> None:
    """Role users can login; currencies include USD/EUR."""
    db = SessionLocal()
    try:
        run_seed(db)
        run_demo_seed(db)
    finally:
        db.close()

    sales = client.post(
        "/api/v1/auth/login",
        json={"username": "sales_us", "password": "demo123"},
    )
    assert sales.status_code == 200
    assert "sales.write" in sales.json()["data"]["user"]["permissions"] or "*" in sales.json()[
        "data"
    ]["user"]["permissions"]
    sales_companies = sales.json()["data"]["user"]["companies"]
    assert {c["code"] for c in sales_companies} == {"USCO"}

    admin = client.post(
        "/api/v1/auth/login",
        json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
    )
    token = admin.json()["data"]["access_token"]
    currencies = client.get(
        "/api/v1/master/currencies",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert currencies.status_code == 200
    codes = {c["code"] for c in currencies.json()["data"]}
    assert {"CNY", "USD", "EUR", "HKD"} <= codes
