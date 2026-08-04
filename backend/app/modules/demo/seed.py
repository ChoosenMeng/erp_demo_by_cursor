"""Demo master + transactional fake data for USCO / EUCO."""

from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.finance.hooks import register_finance_hooks
from app.modules.finance.models import ApBill, ArBill
from app.modules.finance.schemas import PaymentCreate, ReceiptCreate
from app.modules.finance import services as finance_services
from app.modules.inventory import services as inv_services
from app.modules.master.models import Customer, Material, Supplier, Warehouse
from app.modules.master.services import ensure_currencies
from app.modules.org.models import Company, User
from app.modules.trade.models import PurchaseOrder
from app.modules.trade.schemas import (
    OrderLineIn,
    PurchaseOrderCreate,
    SalesOrderCreate,
    StockInCreate,
    StockInLineIn,
    StockOutCreate,
    StockOutLineIn,
)
from app.modules.trade import services as trade_services

SEED_MARK = "SEED-DEMO-BUNDLE"
ACTIVE_CODES = ("USCO", "EUCO")

# Rich master catalog per active company
COMPANY_CATALOG: dict[str, dict] = {
    "USCO": {
        "currency": "USD",
        "customers": [
            ("CUS001", "US Retail Partner", "Alice", "12125550101"),
            ("CUS002", "West Coast Distributors", "Bob", "13105550202"),
            ("CUS003", "Midwest Wholesale LLC", "Carol", "13125550303"),
        ],
        "suppliers": [
            ("SUP001", "US Parts Supplier", "Dave", "14155550404"),
            ("SUP002", "Pacific Components Inc", "Eve", "14155550505"),
        ],
        "materials": [
            ("FG-001", "Finished Good A (US)", "finished", "pcs"),
            ("FG-002", "Finished Good B (US)", "finished", "pcs"),
            ("RM-001", "Aluminum Sheet", "raw", "kg"),
            ("RM-002", "Copper Wire", "raw", "m"),
            ("PK-001", "Carton Box L", "other", "pcs"),
        ],
        "warehouses": [
            ("WH-MAIN", "LA Main WH", True),
            ("WH-EAST", "NJ East WH", False),
        ],
        "po_qty": Decimal("100"),
        "po_price": Decimal("12.50"),
        "so_qty": Decimal("30"),
        "so_price": Decimal("22.00"),
        "extra_stock": Decimal("50"),
    },
    "EUCO": {
        "currency": "EUR",
        "customers": [
            ("CUS001", "EU Trade Customer", "Hans", "491511000001"),
            ("CUS002", "Berlin Retail GmbH", "Greta", "491511000002"),
            ("CUS003", "Paris Distribution SA", "Luc", "33140000003"),
        ],
        "suppliers": [
            ("SUP001", "EU Components GmbH", "Ingrid", "491511000010"),
            ("SUP002", "Nordic Metals AB", "Johan", "46800000011"),
        ],
        "materials": [
            ("FG-001", "Fertigprodukt A", "finished", "pcs"),
            ("FG-002", "Fertigprodukt B", "finished", "pcs"),
            ("RM-001", "Aluminiumblech", "raw", "kg"),
            ("RM-002", "Kupferdraht", "raw", "m"),
            ("PK-001", "Karton L", "other", "pcs"),
        ],
        "warehouses": [
            ("WH-MAIN", "Berlin Lager", True),
            ("WH-SOUTH", "Munich Lager", False),
        ],
        "po_qty": Decimal("80"),
        "po_price": Decimal("11.00"),
        "so_qty": Decimal("25"),
        "so_price": Decimal("19.50"),
        "extra_stock": Decimal("40"),
    },
}


def _get_or_create_customer(
    db: Session, company_id: int, code: str, name: str, contact: str, phone: str
) -> Customer:
    row = db.scalar(
        select(Customer).where(Customer.company_id == company_id, Customer.code == code)
    )
    if row:
        row.name = name
        row.status = "active"
        return row
    row = Customer(
        company_id=company_id,
        code=code,
        name=name,
        contact_name=contact,
        contact_phone=phone,
        status="active",
    )
    db.add(row)
    db.flush()
    return row


def _get_or_create_supplier(
    db: Session, company_id: int, code: str, name: str, contact: str, phone: str
) -> Supplier:
    row = db.scalar(
        select(Supplier).where(Supplier.company_id == company_id, Supplier.code == code)
    )
    if row:
        row.name = name
        row.status = "active"
        return row
    row = Supplier(
        company_id=company_id,
        code=code,
        name=name,
        contact_name=contact,
        contact_phone=phone,
        status="active",
    )
    db.add(row)
    db.flush()
    return row


def _get_or_create_material(
    db: Session,
    company_id: int,
    code: str,
    name: str,
    *,
    material_type: str,
    uom: str,
) -> Material:
    row = db.scalar(
        select(Material).where(Material.company_id == company_id, Material.code == code)
    )
    if row:
        row.name = name
        row.status = "active"
        return row
    row = Material(
        company_id=company_id,
        code=code,
        name=name,
        uom=uom,
        material_type=material_type,
        status="active",
    )
    db.add(row)
    db.flush()
    return row


def _get_or_create_warehouse(
    db: Session, company_id: int, code: str, name: str, *, is_default: bool
) -> Warehouse:
    row = db.scalar(
        select(Warehouse).where(Warehouse.company_id == company_id, Warehouse.code == code)
    )
    if row:
        row.name = name
        row.status = "active"
        if is_default:
            for wh in db.scalars(
                select(Warehouse).where(
                    Warehouse.company_id == company_id, Warehouse.is_default.is_(True)
                )
            ).all():
                if wh.id != row.id:
                    wh.is_default = False
            row.is_default = True
        return row
    if is_default:
        for wh in db.scalars(
            select(Warehouse).where(
                Warehouse.company_id == company_id, Warehouse.is_default.is_(True)
            )
        ).all():
            wh.is_default = False
    row = Warehouse(
        company_id=company_id,
        code=code,
        name=name,
        is_default=is_default,
        status="active",
    )
    db.add(row)
    db.flush()
    return row


def seed_company_master(db: Session, company: Company) -> dict:
    """Seed rich master data for one active company."""
    catalog = COMPANY_CATALOG[company.code]
    customers = [
        _get_or_create_customer(db, company.id, code, name, contact, phone)
        for code, name, contact, phone in catalog["customers"]
    ]
    suppliers = [
        _get_or_create_supplier(db, company.id, code, name, contact, phone)
        for code, name, contact, phone in catalog["suppliers"]
    ]
    materials = [
        _get_or_create_material(
            db, company.id, code, name, material_type=mtype, uom=uom
        )
        for code, name, mtype, uom in catalog["materials"]
    ]
    warehouses = [
        _get_or_create_warehouse(db, company.id, code, name, is_default=is_def)
        for code, name, is_def in catalog["warehouses"]
    ]
    db.flush()
    return {
        "company_code": company.code,
        "base_currency": company.base_currency_code,
        "customer_ids": [c.id for c in customers],
        "supplier_ids": [s.id for s in suppliers],
        "material_ids": [m.id for m in materials],
        "warehouse_ids": [w.id for w in warehouses],
        "customer_id": customers[0].id,
        "supplier_id": suppliers[0].id,
        "warehouse_id": next(w.id for w in warehouses if w.is_default),
        "fg_id": next(m.id for m in materials if m.code == "FG-001"),
        "rm_id": next(m.id for m in materials if m.code == "RM-001"),
    }


def _bundle_exists(db: Session, company_id: int) -> bool:
    return (
        db.scalar(
            select(PurchaseOrder.id).where(
                PurchaseOrder.company_id == company_id,
                PurchaseOrder.remark == SEED_MARK,
            )
        )
        is not None
    )


def seed_company_transactions(
    db: Session, company: Company, master: dict, actor_id: int
) -> dict:
    """Create PO→stock-in, SO→stock-out, inventory and finance side-effects."""
    if _bundle_exists(db, company.id):
        return {"skipped": True, "company_code": company.code}

    catalog = COMPANY_CATALOG[company.code]
    currency = catalog["currency"]
    today = date.today()
    company_id = company.id
    supplier_id = master["supplier_id"]
    customer_id = master["customer_id"]
    warehouse_id = master["warehouse_id"]
    fg_id = master["fg_id"]
    rm_id = master["rm_id"]

    # Opening stock on FG/RM (adjust) so sales can ship even before PO completes
    inv_services.increase(
        db,
        company_id=company_id,
        warehouse_id=warehouse_id,
        material_id=fg_id,
        qty=catalog["extra_stock"],
        actor_id=actor_id,
        tx_type="adjust",
        remark=SEED_MARK,
        commit=True,
    )
    inv_services.increase(
        db,
        company_id=company_id,
        warehouse_id=warehouse_id,
        material_id=rm_id,
        qty=catalog["extra_stock"],
        actor_id=actor_id,
        tx_type="adjust",
        remark=SEED_MARK,
        commit=True,
    )

    po = trade_services.create_purchase_order(
        db,
        company_id,
        PurchaseOrderCreate(
            supplier_id=supplier_id,
            order_date=today - timedelta(days=3),
            currency_code=currency,
            exchange_rate=Decimal("1"),
            remark=SEED_MARK,
            lines=[
                OrderLineIn(
                    material_id=fg_id,
                    qty=catalog["po_qty"],
                    unit_price=catalog["po_price"],
                ),
                OrderLineIn(
                    material_id=rm_id,
                    qty=catalog["po_qty"],
                    unit_price=catalog["po_price"] / Decimal("2"),
                ),
            ],
        ),
        actor_id,
    )
    po = trade_services.confirm_purchase_order(db, company_id, po.id, actor_id)

    stock_in = trade_services.create_stock_in(
        db,
        company_id,
        StockInCreate(
            warehouse_id=warehouse_id,
            po_id=po.id,
            remark=SEED_MARK,
            lines=[
                StockInLineIn(
                    po_line_id=ln.id, material_id=ln.material_id, qty=ln.qty
                )
                for ln in po.lines
            ],
        ),
        actor_id,
    )
    stock_in = trade_services.post_stock_in(db, company_id, stock_in.id, actor_id)

    so = trade_services.create_sales_order(
        db,
        company_id,
        SalesOrderCreate(
            customer_id=customer_id,
            order_date=today - timedelta(days=1),
            currency_code=currency,
            exchange_rate=Decimal("1"),
            remark=SEED_MARK,
            lines=[
                OrderLineIn(
                    material_id=fg_id,
                    qty=catalog["so_qty"],
                    unit_price=catalog["so_price"],
                )
            ],
        ),
        actor_id,
    )
    so = trade_services.confirm_sales_order(db, company_id, so.id, actor_id)

    stock_out = trade_services.create_stock_out(
        db,
        company_id,
        StockOutCreate(
            warehouse_id=warehouse_id,
            so_id=so.id,
            remark=SEED_MARK,
            lines=[
                StockOutLineIn(
                    so_line_id=so.lines[0].id,
                    material_id=fg_id,
                    qty=catalog["so_qty"],
                )
            ],
        ),
        actor_id,
    )
    stock_out = trade_services.post_stock_out(db, company_id, stock_out.id, actor_id)

    # Partial AP payment + AR receipt so finance screens have activity
    ap = db.scalar(
        select(ApBill).where(
            ApBill.company_id == company_id,
            ApBill.source_type == "stock_in",
            ApBill.source_id == stock_in.id,
        )
    )
    if ap and Decimal(ap.paid_amount) == 0:
        pay_amt = (Decimal(ap.amount) / Decimal("2")).quantize(Decimal("0.01"))
        if pay_amt > 0:
            finance_services.register_payment(
                db,
                company_id,
                ap.id,
                PaymentCreate(amount=pay_amt, pay_date=today, remark=SEED_MARK),
                actor_id,
            )

    ar = db.scalar(
        select(ArBill).where(
            ArBill.company_id == company_id,
            ArBill.source_type == "stock_out",
            ArBill.source_id == stock_out.id,
        )
    )
    if ar and Decimal(ar.received_amount) == 0:
        recv_amt = (Decimal(ar.amount) / Decimal("2")).quantize(Decimal("0.01"))
        if recv_amt > 0:
            finance_services.register_receipt(
                db,
                company_id,
                ar.id,
                ReceiptCreate(amount=recv_amt, pay_date=today, remark=SEED_MARK),
                actor_id,
            )

    # Draft SO for pending dashboard count
    trade_services.create_sales_order(
        db,
        company_id,
        SalesOrderCreate(
            customer_id=master["customer_ids"][1],
            order_date=today,
            currency_code=currency,
            exchange_rate=Decimal("1"),
            remark=f"{SEED_MARK}-DRAFT",
            lines=[
                OrderLineIn(
                    material_id=master["material_ids"][1],
                    qty=Decimal("10"),
                    unit_price=catalog["so_price"],
                )
            ],
        ),
        actor_id,
    )

    return {
        "skipped": False,
        "company_code": company.code,
        "po_id": po.id,
        "so_id": so.id,
        "stock_in_id": stock_in.id,
        "stock_out_id": stock_out.id,
    }


def seed_second_company(db: Session, admin_user_id: int) -> Company:
    """Compatibility helper."""
    del admin_user_id
    company = db.scalar(select(Company).where(Company.code == "USCO"))
    if company is None:
        raise RuntimeError("USCO company missing; run org seed first")
    seed_company_master(db, company)
    return company


def run_demo_seed(db: Session, *, with_second_company: bool = True) -> dict:
    """Seed USCO/EUCO master + full business fake data."""
    del with_second_company
    ensure_currencies(db)
    register_finance_hooks()

    companies = db.scalars(
        select(Company).where(
            Company.status == "active",
            Company.code.in_(ACTIVE_CODES),
        )
    ).all()
    if len(companies) < 2:
        raise RuntimeError("USCO/EUCO missing or inactive; run org seed first")

    admin = db.scalar(select(User).where(User.username == "admin"))
    if admin is None:
        raise RuntimeError("admin missing; run org seed first")

    masters = []
    transactions = []
    for company in sorted(companies, key=lambda c: c.code):
        master = seed_company_master(db, company)
        db.commit()
        masters.append(master)
        transactions.append(
            seed_company_transactions(db, company, master, admin.id)
        )

    usco = next(m for m in masters if m["company_code"] == "USCO")
    euco = next((m for m in masters if m["company_code"] == "EUCO"), None)

    return {
        "company_id": next(c.id for c in companies if c.code == "USCO"),
        "company_code": "USCO",
        "master": usco,
        "masters": masters,
        "transactions": transactions,
        "second_company_id": next(c.id for c in companies if c.code == "EUCO"),
        "second_company_code": "EUCO",
        "companies": [c.code for c in companies],
        "material_counts": {
            m["company_code"]: len(m["material_ids"]) for m in masters
        },
        "euco_master": euco,
    }
