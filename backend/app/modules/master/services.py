"""Master-data CRUD services (company-scoped)."""

from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import AppError, NotFoundError
from app.modules.master.models import Currency, Customer, Material, Supplier, Warehouse
from app.modules.master.schemas import (
    CurrencyCreate,
    CurrencyOut,
    CustomerCreate,
    CustomerOut,
    CustomerUpdate,
    MaterialCreate,
    MaterialOut,
    MaterialUpdate,
    PageMeta,
    SupplierCreate,
    SupplierOut,
    SupplierUpdate,
    WarehouseCreate,
    WarehouseOut,
    WarehouseUpdate,
)


def _page_meta(total: int, page: int, page_size: int) -> PageMeta:
    """Build pagination meta."""
    return PageMeta(page=page, page_size=page_size, total=total)


# Demo currencies for multi-currency MVP
DEMO_CURRENCIES: list[tuple[str, str, str | None, int]] = [
    ("CNY", "人民币", "¥", 2),
    ("USD", "美元", "$", 2),
    ("EUR", "欧元", "€", 2),
    ("HKD", "港币", "HK$", 2),
]


def ensure_currency_cny(db: Session, actor_id: int | None = None) -> Currency:
    """Ensure CNY exists (idempotent)."""
    return ensure_currencies(db, actor_id=actor_id)["CNY"]


def ensure_currencies(
    db: Session, actor_id: int | None = None
) -> dict[str, Currency]:
    """Ensure demo currencies exist (CNY/USD/EUR/HKD)."""
    result: dict[str, Currency] = {}
    for code, name, symbol, decimals in DEMO_CURRENCIES:
        row = db.get(Currency, code)
        if row is None:
            row = Currency(
                code=code,
                name=name,
                symbol=symbol,
                decimal_places=decimals,
                status="active",
                created_by=actor_id,
                updated_by=actor_id,
            )
            db.add(row)
            db.flush()
        result[code] = row
    return result


def list_currencies(db: Session) -> list[CurrencyOut]:
    """List all currencies."""
    rows = db.scalars(select(Currency).order_by(Currency.code)).all()
    return [
        CurrencyOut(
            code=r.code,
            name=r.name,
            symbol=r.symbol,
            decimal_places=r.decimal_places,
            status=r.status,
        )
        for r in rows
    ]


def create_currency(db: Session, body: CurrencyCreate, actor_id: int) -> CurrencyOut:
    """Create a currency code."""
    if db.get(Currency, body.code.upper()):
        raise AppError("币种编码已存在", code=40001)
    row = Currency(
        code=body.code.upper(),
        name=body.name,
        symbol=body.symbol,
        decimal_places=body.decimal_places,
        status=body.status,
        created_by=actor_id,
        updated_by=actor_id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return CurrencyOut(
        code=row.code,
        name=row.name,
        symbol=row.symbol,
        decimal_places=row.decimal_places,
        status=row.status,
    )


def _customer_out(row: Customer) -> CustomerOut:
    return CustomerOut(
        id=row.id,
        company_id=row.company_id,
        code=row.code,
        name=row.name,
        contact_name=row.contact_name,
        contact_phone=row.contact_phone,
        credit_limit=row.credit_limit,
        status=row.status,
    )


def list_customers(
    db: Session, company_id: int, *, page: int, page_size: int
) -> dict:
    """Paginated customers for company."""
    total = db.scalar(
        select(func.count()).select_from(Customer).where(Customer.company_id == company_id)
    ) or 0
    rows = db.scalars(
        select(Customer)
        .where(Customer.company_id == company_id)
        .order_by(Customer.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return {"items": [_customer_out(r) for r in rows], "meta": _page_meta(total, page, page_size)}


def create_customer(
    db: Session, company_id: int, body: CustomerCreate, actor_id: int
) -> CustomerOut:
    """Create customer; code unique within company."""
    exists = db.scalar(
        select(Customer.id).where(
            Customer.company_id == company_id, Customer.code == body.code
        )
    )
    if exists:
        raise AppError("客户编码已存在", code=40001)
    row = Customer(
        company_id=company_id,
        code=body.code,
        name=body.name,
        contact_name=body.contact_name,
        contact_phone=body.contact_phone,
        credit_limit=body.credit_limit,
        status=body.status,
        created_by=actor_id,
        updated_by=actor_id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _customer_out(row)


def get_customer(db: Session, company_id: int, customer_id: int) -> CustomerOut:
    """Get customer in company scope."""
    row = db.get(Customer, customer_id)
    if row is None or row.company_id != company_id:
        raise NotFoundError("客户不存在")
    return _customer_out(row)


def update_customer(
    db: Session,
    company_id: int,
    customer_id: int,
    body: CustomerUpdate,
    actor_id: int,
) -> CustomerOut:
    """Patch customer fields."""
    row = db.get(Customer, customer_id)
    if row is None or row.company_id != company_id:
        raise NotFoundError("客户不存在")
    data = body.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(row, key, value)
    row.updated_by = actor_id
    db.commit()
    db.refresh(row)
    return _customer_out(row)


def delete_customer(db: Session, company_id: int, customer_id: int, actor_id: int) -> None:
    """Soft-delete by setting status inactive."""
    row = db.get(Customer, customer_id)
    if row is None or row.company_id != company_id:
        raise NotFoundError("客户不存在")
    row.status = "inactive"
    row.updated_by = actor_id
    db.commit()


def _supplier_out(row: Supplier) -> SupplierOut:
    return SupplierOut(
        id=row.id,
        company_id=row.company_id,
        code=row.code,
        name=row.name,
        contact_name=row.contact_name,
        contact_phone=row.contact_phone,
        status=row.status,
    )


def list_suppliers(
    db: Session, company_id: int, *, page: int, page_size: int
) -> dict:
    """Paginated suppliers for company."""
    total = db.scalar(
        select(func.count()).select_from(Supplier).where(Supplier.company_id == company_id)
    ) or 0
    rows = db.scalars(
        select(Supplier)
        .where(Supplier.company_id == company_id)
        .order_by(Supplier.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return {"items": [_supplier_out(r) for r in rows], "meta": _page_meta(total, page, page_size)}


def create_supplier(
    db: Session, company_id: int, body: SupplierCreate, actor_id: int
) -> SupplierOut:
    """Create supplier; code unique within company."""
    exists = db.scalar(
        select(Supplier.id).where(
            Supplier.company_id == company_id, Supplier.code == body.code
        )
    )
    if exists:
        raise AppError("供应商编码已存在", code=40001)
    row = Supplier(
        company_id=company_id,
        code=body.code,
        name=body.name,
        contact_name=body.contact_name,
        contact_phone=body.contact_phone,
        status=body.status,
        created_by=actor_id,
        updated_by=actor_id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _supplier_out(row)


def get_supplier(db: Session, company_id: int, supplier_id: int) -> SupplierOut:
    """Get supplier in company scope."""
    row = db.get(Supplier, supplier_id)
    if row is None or row.company_id != company_id:
        raise NotFoundError("供应商不存在")
    return _supplier_out(row)


def update_supplier(
    db: Session,
    company_id: int,
    supplier_id: int,
    body: SupplierUpdate,
    actor_id: int,
) -> SupplierOut:
    """Patch supplier fields."""
    row = db.get(Supplier, supplier_id)
    if row is None or row.company_id != company_id:
        raise NotFoundError("供应商不存在")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(row, key, value)
    row.updated_by = actor_id
    db.commit()
    db.refresh(row)
    return _supplier_out(row)


def delete_supplier(db: Session, company_id: int, supplier_id: int, actor_id: int) -> None:
    """Soft-delete supplier."""
    row = db.get(Supplier, supplier_id)
    if row is None or row.company_id != company_id:
        raise NotFoundError("供应商不存在")
    row.status = "inactive"
    row.updated_by = actor_id
    db.commit()


def _material_out(row: Material) -> MaterialOut:
    return MaterialOut(
        id=row.id,
        company_id=row.company_id,
        code=row.code,
        name=row.name,
        spec=row.spec,
        uom=row.uom,
        material_type=row.material_type,
        status=row.status,
    )


def list_materials(
    db: Session, company_id: int, *, page: int, page_size: int
) -> dict:
    """Paginated materials for company."""
    total = db.scalar(
        select(func.count()).select_from(Material).where(Material.company_id == company_id)
    ) or 0
    rows = db.scalars(
        select(Material)
        .where(Material.company_id == company_id)
        .order_by(Material.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return {"items": [_material_out(r) for r in rows], "meta": _page_meta(total, page, page_size)}


def create_material(
    db: Session, company_id: int, body: MaterialCreate, actor_id: int
) -> MaterialOut:
    """Create material; code unique within company."""
    exists = db.scalar(
        select(Material.id).where(
            Material.company_id == company_id, Material.code == body.code
        )
    )
    if exists:
        raise AppError("物料编码已存在", code=40001)
    row = Material(
        company_id=company_id,
        code=body.code,
        name=body.name,
        spec=body.spec,
        uom=body.uom,
        material_type=body.material_type,
        status=body.status,
        created_by=actor_id,
        updated_by=actor_id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _material_out(row)


def get_material(db: Session, company_id: int, material_id: int) -> MaterialOut:
    """Get material in company scope."""
    row = db.get(Material, material_id)
    if row is None or row.company_id != company_id:
        raise NotFoundError("物料不存在")
    return _material_out(row)


def update_material(
    db: Session,
    company_id: int,
    material_id: int,
    body: MaterialUpdate,
    actor_id: int,
) -> MaterialOut:
    """Patch material fields."""
    row = db.get(Material, material_id)
    if row is None or row.company_id != company_id:
        raise NotFoundError("物料不存在")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(row, key, value)
    row.updated_by = actor_id
    db.commit()
    db.refresh(row)
    return _material_out(row)


def delete_material(db: Session, company_id: int, material_id: int, actor_id: int) -> None:
    """Soft-delete material."""
    row = db.get(Material, material_id)
    if row is None or row.company_id != company_id:
        raise NotFoundError("物料不存在")
    row.status = "inactive"
    row.updated_by = actor_id
    db.commit()


def _warehouse_out(row: Warehouse) -> WarehouseOut:
    return WarehouseOut(
        id=row.id,
        company_id=row.company_id,
        code=row.code,
        name=row.name,
        is_default=row.is_default,
        status=row.status,
    )


def _clear_default_warehouses(db: Session, company_id: int, except_id: int | None = None) -> None:
    """Ensure at most one default warehouse per company."""
    q = select(Warehouse).where(
        Warehouse.company_id == company_id, Warehouse.is_default.is_(True)
    )
    if except_id is not None:
        q = q.where(Warehouse.id != except_id)
    for wh in db.scalars(q).all():
        wh.is_default = False


def list_warehouses(
    db: Session, company_id: int, *, page: int, page_size: int
) -> dict:
    """Paginated warehouses for company."""
    total = db.scalar(
        select(func.count()).select_from(Warehouse).where(Warehouse.company_id == company_id)
    ) or 0
    rows = db.scalars(
        select(Warehouse)
        .where(Warehouse.company_id == company_id)
        .order_by(Warehouse.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return {
        "items": [_warehouse_out(r) for r in rows],
        "meta": _page_meta(total, page, page_size),
    }


def create_warehouse(
    db: Session, company_id: int, body: WarehouseCreate, actor_id: int
) -> WarehouseOut:
    """Create warehouse; optionally set as default."""
    exists = db.scalar(
        select(Warehouse.id).where(
            Warehouse.company_id == company_id, Warehouse.code == body.code
        )
    )
    if exists:
        raise AppError("仓库编码已存在", code=40001)
    if body.is_default:
        _clear_default_warehouses(db, company_id)
    row = Warehouse(
        company_id=company_id,
        code=body.code,
        name=body.name,
        is_default=body.is_default,
        status=body.status,
        created_by=actor_id,
        updated_by=actor_id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _warehouse_out(row)


def get_warehouse(db: Session, company_id: int, warehouse_id: int) -> WarehouseOut:
    """Get warehouse in company scope."""
    row = db.get(Warehouse, warehouse_id)
    if row is None or row.company_id != company_id:
        raise NotFoundError("仓库不存在")
    return _warehouse_out(row)


def update_warehouse(
    db: Session,
    company_id: int,
    warehouse_id: int,
    body: WarehouseUpdate,
    actor_id: int,
) -> WarehouseOut:
    """Patch warehouse fields."""
    row = db.get(Warehouse, warehouse_id)
    if row is None or row.company_id != company_id:
        raise NotFoundError("仓库不存在")
    data = body.model_dump(exclude_unset=True)
    if data.get("is_default") is True:
        _clear_default_warehouses(db, company_id, except_id=row.id)
    for key, value in data.items():
        setattr(row, key, value)
    row.updated_by = actor_id
    db.commit()
    db.refresh(row)
    return _warehouse_out(row)
