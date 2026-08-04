"""M4 finance bill generation and payment tests."""

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


def test_stock_post_creates_bills_and_rejects_overpay() -> None:
    """Stock-in→AP, stock-out→AR; overpay rejected."""
    headers = _headers()
    suffix = uuid4().hex[:8]

    supplier = client.post(
        "/api/v1/master/suppliers",
        headers=headers,
        json={"code": f"FS-{suffix}", "name": "财务供应商"},
    ).json()["data"]["id"]
    customer = client.post(
        "/api/v1/master/customers",
        headers=headers,
        json={"code": f"FC-{suffix}", "name": "财务客户"},
    ).json()["data"]["id"]
    material = client.post(
        "/api/v1/master/materials",
        headers=headers,
        json={
            "code": f"FM-{suffix}",
            "name": "财务物料",
            "uom": "pcs",
            "material_type": "finished",
        },
    ).json()["data"]["id"]
    warehouse = client.post(
        "/api/v1/master/warehouses",
        headers=headers,
        json={"code": f"FW-{suffix}", "name": "财务仓"},
    ).json()["data"]["id"]

    po = client.post(
        "/api/v1/purchase/orders",
        headers=headers,
        json={
            "supplier_id": supplier,
            "order_date": "2026-08-05",
            "lines": [{"material_id": material, "qty": "10", "unit_price": "5"}],
        },
    ).json()["data"]
    client.post(f"/api/v1/purchase/orders/{po['id']}/confirm", headers=headers)
    stock_in = client.post(
        "/api/v1/purchase/stock-ins",
        headers=headers,
        json={
            "warehouse_id": warehouse,
            "po_id": po["id"],
            "lines": [
                {
                    "po_line_id": po["lines"][0]["id"],
                    "material_id": material,
                    "qty": "10",
                }
            ],
        },
    ).json()["data"]
    assert (
        client.post(
            f"/api/v1/purchase/stock-ins/{stock_in['id']}/post", headers=headers
        ).status_code
        == 200
    )

    ap_list = client.get("/api/v1/finance/ap-bills", headers=headers)
    assert ap_list.status_code == 200
    ap = next(i for i in ap_list.json()["data"]["items"] if i["source_id"] == stock_in["id"])
    assert Decimal(ap["amount"]) == Decimal("50.00")
    assert ap["status"] == "open"

    over = client.post(
        f"/api/v1/finance/ap-bills/{ap['id']}/payments",
        headers=headers,
        json={"amount": "999", "pay_date": "2026-08-05"},
    )
    assert over.status_code == 400
    assert over.json()["code"] == 40022

    pay = client.post(
        f"/api/v1/finance/ap-bills/{ap['id']}/payments",
        headers=headers,
        json={"amount": "50", "pay_date": "2026-08-05"},
    )
    assert pay.status_code == 200
    assert pay.json()["data"]["bill"]["status"] == "paid"

    so = client.post(
        "/api/v1/sales/orders",
        headers=headers,
        json={
            "customer_id": customer,
            "order_date": "2026-08-05",
            "lines": [{"material_id": material, "qty": "2", "unit_price": "9"}],
        },
    ).json()["data"]
    client.post(f"/api/v1/sales/orders/{so['id']}/confirm", headers=headers)
    stock_out = client.post(
        "/api/v1/sales/stock-outs",
        headers=headers,
        json={
            "warehouse_id": warehouse,
            "so_id": so["id"],
            "lines": [
                {
                    "so_line_id": so["lines"][0]["id"],
                    "material_id": material,
                    "qty": "2",
                }
            ],
        },
    ).json()["data"]
    assert (
        client.post(
            f"/api/v1/sales/stock-outs/{stock_out['id']}/post", headers=headers
        ).status_code
        == 200
    )

    ar_list = client.get("/api/v1/finance/ar-bills", headers=headers)
    ar = next(i for i in ar_list.json()["data"]["items"] if i["source_id"] == stock_out["id"])
    assert Decimal(ar["amount"]) == Decimal("18.00")

    dash = client.get("/api/v1/dashboard/summary", headers=headers)
    assert dash.status_code == 200
    assert "sales_amount_month" in dash.json()["data"]
