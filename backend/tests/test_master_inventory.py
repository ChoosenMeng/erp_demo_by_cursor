"""M2 master data and inventory service tests."""

from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.exceptions import AppError
from app.db.session import SessionLocal
from app.main import app
from app.modules.inventory import services as inv_services
from app.modules.org.seed import ADMIN_PASSWORD, ADMIN_USERNAME

client = TestClient(app)


def _auth_headers() -> dict[str, str]:
    login = client.post(
        "/api/v1/auth/login",
        json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
    )
    assert login.status_code == 200
    token = login.json()["data"]["access_token"]
    company_id = login.json()["data"]["user"]["company_id"]
    return {
        "Authorization": f"Bearer {token}",
        "X-Company-Id": str(company_id),
    }


def test_master_material_unique_code() -> None:
    """Duplicate material code within company is rejected."""
    headers = _auth_headers()
    code = f"M2-UT-{uuid4().hex[:8]}"
    first = client.post(
        "/api/v1/master/materials",
        headers=headers,
        json={
            "code": code,
            "name": "UT Material",
            "uom": "pcs",
            "material_type": "raw",
        },
    )
    assert first.status_code == 200

    dup = client.post(
        "/api/v1/master/materials",
        headers=headers,
        json={
            "code": code,
            "name": "UT Material Dup",
            "uom": "pcs",
            "material_type": "raw",
        },
    )
    assert dup.status_code == 400
    assert dup.json()["code"] == 40001


def test_inventory_increase_and_insufficient_decrease() -> None:
    """Increase updates balance; oversell raises and rolls back."""
    headers = _auth_headers()

    suffix = uuid4().hex[:8]
    wh = client.post(
        "/api/v1/master/warehouses",
        headers=headers,
        json={"code": f"WH-{suffix}", "name": "UT仓", "is_default": False},
    )
    assert wh.status_code == 200
    warehouse_id = wh.json()["data"]["id"]

    mat = client.post(
        "/api/v1/master/materials",
        headers=headers,
        json={
            "code": f"MAT-{suffix}",
            "name": "库存测试料",
            "uom": "pcs",
            "material_type": "finished",
        },
    )
    assert mat.status_code == 200
    material_id = mat.json()["data"]["id"]

    up = client.post(
        "/api/v1/inventory/adjust",
        headers=headers,
        json={
            "warehouse_id": warehouse_id,
            "material_id": material_id,
            "direction": 1,
            "qty": "10",
            "remark": "ut in",
        },
    )
    assert up.status_code == 200
    assert Decimal(up.json()["data"]["qty_on_hand"]) == Decimal("10")

    # Direct service call: insufficient stock must leave balance unchanged after rollback
    db: Session = SessionLocal()
    try:
        company_id = int(headers["X-Company-Id"])
        try:
            inv_services.decrease(
                db,
                company_id=company_id,
                warehouse_id=warehouse_id,
                material_id=material_id,
                qty=Decimal("999"),
                actor_id=1,
            )
            raise AssertionError("expected AppError")
        except AppError as exc:
            assert "库存不足" in exc.message
            db.rollback()

        bal = client.get(
            f"/api/v1/inventory/balances?warehouse_id={warehouse_id}&material_id={material_id}",
            headers=headers,
        )
        assert bal.status_code == 200
        items = bal.json()["data"]["items"]
        assert len(items) == 1
        assert Decimal(items[0]["qty_available"]) == Decimal("10")
    finally:
        db.close()

    bad = client.post(
        "/api/v1/inventory/adjust",
        headers=headers,
        json={
            "warehouse_id": warehouse_id,
            "material_id": material_id,
            "direction": -1,
            "qty": "999",
            "remark": "ut oversell",
        },
    )
    assert bad.status_code == 400
    assert bad.json()["code"] == 40002
