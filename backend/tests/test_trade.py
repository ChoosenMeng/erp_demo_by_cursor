"""M3 purchase/sales stock posting flow tests."""

from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.modules.org.seed import ADMIN_PASSWORD, ADMIN_USERNAME

client = TestClient(app)


def _headers() -> dict[str, str]:
    login = client.post(
        "/api/v1/auth/login",
        json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
    )
    assert login.status_code == 200
    data = login.json()["data"]
    return {
        "Authorization": f"Bearer {data['access_token']}",
        "X-Company-Id": str(data["user"]["company_id"]),
    }


def _seed_master(headers: dict[str, str]) -> tuple[int, int, int, int]:
    """Create supplier/customer/material/warehouse for one test run."""
    suffix = uuid4().hex[:8]
    supplier = client.post(
        "/api/v1/master/suppliers",
        headers=headers,
        json={"code": f"S-{suffix}", "name": "UT供应商"},
    )
    customer = client.post(
        "/api/v1/master/customers",
        headers=headers,
        json={"code": f"C-{suffix}", "name": "UT客户"},
    )
    material = client.post(
        "/api/v1/master/materials",
        headers=headers,
        json={
            "code": f"M-{suffix}",
            "name": "UT物料",
            "uom": "pcs",
            "material_type": "finished",
        },
    )
    warehouse = client.post(
        "/api/v1/master/warehouses",
        headers=headers,
        json={"code": f"W-{suffix}", "name": "UT仓", "is_default": False},
    )
    assert all(r.status_code == 200 for r in (supplier, customer, material, warehouse))
    return (
        supplier.json()["data"]["id"],
        customer.json()["data"]["id"],
        material.json()["data"]["id"],
        warehouse.json()["data"]["id"],
    )


def test_po_in_so_out_flow_and_oversell() -> None:
    """PO confirm→stock-in→SO confirm→stock-out; oversell rejected."""
    headers = _headers()
    supplier_id, customer_id, material_id, warehouse_id = _seed_master(headers)

    po = client.post(
        "/api/v1/purchase/orders",
        headers=headers,
        json={
            "supplier_id": supplier_id,
            "order_date": "2026-08-05",
            "currency_code": "CNY",
            "lines": [{"material_id": material_id, "qty": "10", "unit_price": "5"}],
        },
    )
    assert po.status_code == 200
    po_id = po.json()["data"]["id"]
    po_line_id = po.json()["data"]["lines"][0]["id"]
    assert po.json()["data"]["doc_no"].startswith("PO")

    conf = client.post(f"/api/v1/purchase/orders/{po_id}/confirm", headers=headers)
    assert conf.status_code == 200
    assert conf.json()["data"]["status"] == "confirmed"

    stock_in = client.post(
        "/api/v1/purchase/stock-ins",
        headers=headers,
        json={
            "warehouse_id": warehouse_id,
            "po_id": po_id,
            "lines": [
                {
                    "po_line_id": po_line_id,
                    "material_id": material_id,
                    "qty": "10",
                }
            ],
        },
    )
    assert stock_in.status_code == 200
    stock_in_id = stock_in.json()["data"]["id"]

    posted = client.post(
        f"/api/v1/purchase/stock-ins/{stock_in_id}/post", headers=headers
    )
    assert posted.status_code == 200
    assert posted.json()["data"]["status"] == "posted"

    bal = client.get(
        f"/api/v1/inventory/balances?warehouse_id={warehouse_id}&material_id={material_id}",
        headers=headers,
    )
    assert bal.status_code == 200
    assert Decimal(bal.json()["data"]["items"][0]["qty_on_hand"]) == Decimal("10")

    so = client.post(
        "/api/v1/sales/orders",
        headers=headers,
        json={
            "customer_id": customer_id,
            "order_date": "2026-08-05",
            "currency_code": "CNY",
            "lines": [{"material_id": material_id, "qty": "4", "unit_price": "9"}],
        },
    )
    assert so.status_code == 200
    so_id = so.json()["data"]["id"]
    so_line_id = so.json()["data"]["lines"][0]["id"]

    assert (
        client.post(f"/api/v1/sales/orders/{so_id}/confirm", headers=headers).status_code
        == 200
    )

    stock_out = client.post(
        "/api/v1/sales/stock-outs",
        headers=headers,
        json={
            "warehouse_id": warehouse_id,
            "so_id": so_id,
            "lines": [
                {
                    "so_line_id": so_line_id,
                    "material_id": material_id,
                    "qty": "4",
                }
            ],
        },
    )
    assert stock_out.status_code == 200
    out_id = stock_out.json()["data"]["id"]
    out_posted = client.post(
        f"/api/v1/sales/stock-outs/{out_id}/post", headers=headers
    )
    assert out_posted.status_code == 200
    assert out_posted.json()["data"]["status"] == "posted"

    bal2 = client.get(
        f"/api/v1/inventory/balances?warehouse_id={warehouse_id}&material_id={material_id}",
        headers=headers,
    )
    assert Decimal(bal2.json()["data"]["items"][0]["qty_on_hand"]) == Decimal("6")

    # Oversell: another SO for 100 pcs should fail on post
    so2 = client.post(
        "/api/v1/sales/orders",
        headers=headers,
        json={
            "customer_id": customer_id,
            "order_date": "2026-08-05",
            "lines": [{"material_id": material_id, "qty": "100", "unit_price": "1"}],
        },
    )
    so2_id = so2.json()["data"]["id"]
    so2_line = so2.json()["data"]["lines"][0]["id"]
    client.post(f"/api/v1/sales/orders/{so2_id}/confirm", headers=headers)
    bad_out = client.post(
        "/api/v1/sales/stock-outs",
        headers=headers,
        json={
            "warehouse_id": warehouse_id,
            "so_id": so2_id,
            "lines": [
                {"so_line_id": so2_line, "material_id": material_id, "qty": "100"}
            ],
        },
    )
    bad_id = bad_out.json()["data"]["id"]
    fail = client.post(f"/api/v1/sales/stock-outs/{bad_id}/post", headers=headers)
    assert fail.status_code == 400
    assert fail.json()["code"] == 40002

    bal3 = client.get(
        f"/api/v1/inventory/balances?warehouse_id={warehouse_id}&material_id={material_id}",
        headers=headers,
    )
    assert Decimal(bal3.json()["data"]["items"][0]["qty_on_hand"]) == Decimal("6")
