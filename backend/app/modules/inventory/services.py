"""Inventory balance / transaction domain services."""

from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import AppError, NotFoundError
from app.modules.inventory.models import InventoryBalance, InventoryTransaction
from app.modules.inventory.schemas import (
    InventoryAdjustRequest,
    InventoryBalanceOut,
    InventoryTransactionOut,
    PageMeta,
)
from app.modules.master.models import Material, Warehouse


def _page_meta(total: int, page: int, page_size: int) -> PageMeta:
    return PageMeta(page=page, page_size=page_size, total=total)


def _get_warehouse(db: Session, company_id: int, warehouse_id: int) -> Warehouse:
    row = db.get(Warehouse, warehouse_id)
    if row is None or row.company_id != company_id:
        raise NotFoundError("仓库不存在")
    return row


def _get_material(db: Session, company_id: int, material_id: int) -> Material:
    row = db.get(Material, material_id)
    if row is None or row.company_id != company_id:
        raise NotFoundError("物料不存在")
    return row


def _get_or_create_balance(
    db: Session,
    company_id: int,
    warehouse_id: int,
    material_id: int,
    actor_id: int | None,
) -> InventoryBalance:
    """Load balance row with row lock; create zero row if missing."""
    row = db.scalar(
        select(InventoryBalance)
        .where(
            InventoryBalance.company_id == company_id,
            InventoryBalance.warehouse_id == warehouse_id,
            InventoryBalance.material_id == material_id,
        )
        .with_for_update()
    )
    if row:
        return row
    row = InventoryBalance(
        company_id=company_id,
        warehouse_id=warehouse_id,
        material_id=material_id,
        qty_on_hand=Decimal("0"),
        qty_available=Decimal("0"),
        created_by=actor_id,
        updated_by=actor_id,
    )
    db.add(row)
    db.flush()
    return row


def increase(
    db: Session,
    *,
    company_id: int,
    warehouse_id: int,
    material_id: int,
    qty: Decimal,
    actor_id: int | None,
    tx_type: str = "in",
    ref_doc_type: str | None = None,
    ref_doc_id: int | None = None,
    ref_doc_no: str | None = None,
    remark: str | None = None,
    commit: bool = False,
) -> InventoryBalance:
    """Increase on-hand/available qty and write ledger row."""
    if qty <= 0:
        raise AppError("数量必须大于 0", code=40001)
    _get_warehouse(db, company_id, warehouse_id)
    _get_material(db, company_id, material_id)

    bal = _get_or_create_balance(db, company_id, warehouse_id, material_id, actor_id)
    bal.qty_on_hand = Decimal(bal.qty_on_hand) + qty
    bal.qty_available = Decimal(bal.qty_available) + qty
    bal.updated_by = actor_id

    db.add(
        InventoryTransaction(
            company_id=company_id,
            warehouse_id=warehouse_id,
            material_id=material_id,
            tx_type=tx_type,
            direction=1,
            qty=qty,
            ref_doc_type=ref_doc_type,
            ref_doc_id=ref_doc_id,
            ref_doc_no=ref_doc_no,
            remark=remark,
            created_by=actor_id,
            updated_by=actor_id,
        )
    )
    db.flush()
    if commit:
        db.commit()
        db.refresh(bal)
    return bal


def decrease(
    db: Session,
    *,
    company_id: int,
    warehouse_id: int,
    material_id: int,
    qty: Decimal,
    actor_id: int | None,
    tx_type: str = "out",
    ref_doc_type: str | None = None,
    ref_doc_id: int | None = None,
    ref_doc_no: str | None = None,
    remark: str | None = None,
    commit: bool = False,
) -> InventoryBalance:
    """Decrease qty; raise and leave session dirty on insufficient stock.

    Caller must rollback the outer transaction on AppError.
    """
    if qty <= 0:
        raise AppError("数量必须大于 0", code=40001)
    _get_warehouse(db, company_id, warehouse_id)
    _get_material(db, company_id, material_id)

    bal = _get_or_create_balance(db, company_id, warehouse_id, material_id, actor_id)
    available = Decimal(bal.qty_available)
    if available < qty:
        raise AppError("库存不足", code=40002, details={"available": str(available)})

    bal.qty_on_hand = Decimal(bal.qty_on_hand) - qty
    bal.qty_available = available - qty
    bal.updated_by = actor_id

    db.add(
        InventoryTransaction(
            company_id=company_id,
            warehouse_id=warehouse_id,
            material_id=material_id,
            tx_type=tx_type,
            direction=-1,
            qty=qty,
            ref_doc_type=ref_doc_type,
            ref_doc_id=ref_doc_id,
            ref_doc_no=ref_doc_no,
            remark=remark,
            created_by=actor_id,
            updated_by=actor_id,
        )
    )
    db.flush()
    if commit:
        db.commit()
        db.refresh(bal)
    return bal


def list_balances(
    db: Session,
    company_id: int,
    *,
    warehouse_id: int | None,
    material_id: int | None,
    page: int,
    page_size: int,
) -> dict:
    """List balances with warehouse/material names."""
    filters = [InventoryBalance.company_id == company_id]
    if warehouse_id is not None:
        filters.append(InventoryBalance.warehouse_id == warehouse_id)
    if material_id is not None:
        filters.append(InventoryBalance.material_id == material_id)

    total = db.scalar(
        select(func.count()).select_from(InventoryBalance).where(*filters)
    ) or 0
    rows = db.execute(
        select(InventoryBalance, Warehouse.name, Material.code, Material.name)
        .join(Warehouse, Warehouse.id == InventoryBalance.warehouse_id)
        .join(Material, Material.id == InventoryBalance.material_id)
        .where(*filters)
        .order_by(InventoryBalance.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    items = [
        InventoryBalanceOut(
            id=bal.id,
            company_id=bal.company_id,
            warehouse_id=bal.warehouse_id,
            warehouse_name=wh_name,
            material_id=bal.material_id,
            material_code=mat_code,
            material_name=mat_name,
            qty_on_hand=bal.qty_on_hand,
            qty_available=bal.qty_available,
        )
        for bal, wh_name, mat_code, mat_name in rows
    ]
    return {"items": items, "meta": _page_meta(total, page, page_size)}


def list_transactions(
    db: Session,
    company_id: int,
    *,
    warehouse_id: int | None,
    material_id: int | None,
    page: int,
    page_size: int,
) -> dict:
    """Paginated inventory ledger."""
    filters = [InventoryTransaction.company_id == company_id]
    if warehouse_id is not None:
        filters.append(InventoryTransaction.warehouse_id == warehouse_id)
    if material_id is not None:
        filters.append(InventoryTransaction.material_id == material_id)

    total = db.scalar(
        select(func.count()).select_from(InventoryTransaction).where(*filters)
    ) or 0
    rows = db.scalars(
        select(InventoryTransaction)
        .where(*filters)
        .order_by(InventoryTransaction.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    items = [
        InventoryTransactionOut(
            id=r.id,
            company_id=r.company_id,
            warehouse_id=r.warehouse_id,
            material_id=r.material_id,
            tx_type=r.tx_type,
            direction=r.direction,
            qty=r.qty,
            ref_doc_type=r.ref_doc_type,
            ref_doc_id=r.ref_doc_id,
            ref_doc_no=r.ref_doc_no,
            remark=r.remark,
        )
        for r in rows
    ]
    return {"items": items, "meta": _page_meta(total, page, page_size)}


def adjust_stock(
    db: Session, company_id: int, body: InventoryAdjustRequest, actor_id: int
) -> InventoryBalanceOut:
    """Debug adjust endpoint: in or out with remark."""
    if body.direction not in (1, -1):
        raise AppError("direction 只能为 1 或 -1", code=40001)

    try:
        if body.direction == 1:
            bal = increase(
                db,
                company_id=company_id,
                warehouse_id=body.warehouse_id,
                material_id=body.material_id,
                qty=body.qty,
                actor_id=actor_id,
                tx_type="adjust",
                remark=body.remark,
            )
        else:
            bal = decrease(
                db,
                company_id=company_id,
                warehouse_id=body.warehouse_id,
                material_id=body.material_id,
                qty=body.qty,
                actor_id=actor_id,
                tx_type="adjust",
                remark=body.remark,
            )
        db.commit()
        db.refresh(bal)
    except AppError:
        db.rollback()
        raise

    wh = _get_warehouse(db, company_id, bal.warehouse_id)
    mat = _get_material(db, company_id, bal.material_id)
    return InventoryBalanceOut(
        id=bal.id,
        company_id=bal.company_id,
        warehouse_id=bal.warehouse_id,
        warehouse_name=wh.name,
        material_id=bal.material_id,
        material_code=mat.code,
        material_name=mat.name,
        qty_on_hand=bal.qty_on_hand,
        qty_available=bal.qty_available,
    )
