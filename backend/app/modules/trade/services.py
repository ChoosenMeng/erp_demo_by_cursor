"""Purchase / sales / stock document services."""

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import AppError, NotFoundError
from app.modules.inventory import services as inv_services
from app.modules.master.models import Customer, Material, Supplier, Warehouse
from app.modules.org.schemas import PageMeta
from app.modules.trade.models import (
    PurchaseOrder,
    PurchaseOrderLine,
    SalesOrder,
    SalesOrderLine,
    StockInOrder,
    StockInOrderLine,
    StockOutOrder,
    StockOutOrderLine,
)
from app.modules.trade.schemas import (
    PurchaseOrderCreate,
    PurchaseOrderOut,
    PurchaseOrderLineOut,
    PurchaseOrderUpdate,
    SalesOrderCreate,
    SalesOrderLineOut,
    SalesOrderOut,
    SalesOrderUpdate,
    StockInCreate,
    StockInLineOut,
    StockInOut,
    StockOutCreate,
    StockOutLineOut,
    StockOutOut,
)
from app.modules.trade.sequences import next_doc_no

# Optional hook set by finance module (M4) to create AP/AR after posting.
# Signature: (db, company_id, doc, actor_id) -> None
after_stock_in_posted = None
after_stock_out_posted = None


def _page_meta(total: int, page: int, page_size: int) -> PageMeta:
    return PageMeta(page=page, page_size=page_size, total=total)


def _money(qty: Decimal, price: Decimal) -> Decimal:
    return (qty * price).quantize(Decimal("0.01"))


def _ensure_supplier(db: Session, company_id: int, supplier_id: int) -> None:
    row = db.get(Supplier, supplier_id)
    if row is None or row.company_id != company_id:
        raise NotFoundError("供应商不存在")


def _ensure_customer(db: Session, company_id: int, customer_id: int) -> None:
    row = db.get(Customer, customer_id)
    if row is None or row.company_id != company_id:
        raise NotFoundError("客户不存在")


def _ensure_material(db: Session, company_id: int, material_id: int) -> None:
    row = db.get(Material, material_id)
    if row is None or row.company_id != company_id:
        raise NotFoundError("物料不存在")


def _ensure_warehouse(db: Session, company_id: int, warehouse_id: int) -> None:
    row = db.get(Warehouse, warehouse_id)
    if row is None or row.company_id != company_id:
        raise NotFoundError("仓库不存在")


def _po_out(order: PurchaseOrder) -> PurchaseOrderOut:
    return PurchaseOrderOut(
        id=order.id,
        company_id=order.company_id,
        doc_no=order.doc_no,
        supplier_id=order.supplier_id,
        status=order.status,
        currency_code=order.currency_code,
        exchange_rate=order.exchange_rate,
        tax_rate=order.tax_rate,
        amount=order.amount,
        base_amount=order.base_amount,
        order_date=order.order_date,
        remark=order.remark,
        lines=[
            PurchaseOrderLineOut(
                id=ln.id,
                line_no=ln.line_no,
                material_id=ln.material_id,
                qty=ln.qty,
                qty_received=ln.qty_received,
                unit_price=ln.unit_price,
                amount=ln.amount,
                base_amount=ln.base_amount,
            )
            for ln in sorted(order.lines, key=lambda x: x.line_no)
        ],
    )


def _so_out(order: SalesOrder) -> SalesOrderOut:
    return SalesOrderOut(
        id=order.id,
        company_id=order.company_id,
        doc_no=order.doc_no,
        customer_id=order.customer_id,
        status=order.status,
        currency_code=order.currency_code,
        exchange_rate=order.exchange_rate,
        tax_rate=order.tax_rate,
        amount=order.amount,
        base_amount=order.base_amount,
        order_date=order.order_date,
        remark=order.remark,
        lines=[
            SalesOrderLineOut(
                id=ln.id,
                line_no=ln.line_no,
                material_id=ln.material_id,
                qty=ln.qty,
                qty_shipped=ln.qty_shipped,
                unit_price=ln.unit_price,
                amount=ln.amount,
                base_amount=ln.base_amount,
            )
            for ln in sorted(order.lines, key=lambda x: x.line_no)
        ],
    )


def _stock_in_out(order: StockInOrder) -> StockInOut:
    return StockInOut(
        id=order.id,
        company_id=order.company_id,
        doc_no=order.doc_no,
        warehouse_id=order.warehouse_id,
        po_id=order.po_id,
        status=order.status,
        posted_at=order.posted_at,
        remark=order.remark,
        lines=[
            StockInLineOut(
                id=ln.id,
                line_no=ln.line_no,
                po_line_id=ln.po_line_id,
                material_id=ln.material_id,
                qty=ln.qty,
            )
            for ln in sorted(order.lines, key=lambda x: x.line_no)
        ],
    )


def _stock_out_out(order: StockOutOrder) -> StockOutOut:
    return StockOutOut(
        id=order.id,
        company_id=order.company_id,
        doc_no=order.doc_no,
        warehouse_id=order.warehouse_id,
        so_id=order.so_id,
        status=order.status,
        posted_at=order.posted_at,
        remark=order.remark,
        lines=[
            StockOutLineOut(
                id=ln.id,
                line_no=ln.line_no,
                so_line_id=ln.so_line_id,
                material_id=ln.material_id,
                qty=ln.qty,
            )
            for ln in sorted(order.lines, key=lambda x: x.line_no)
        ],
    )


def _load_po(db: Session, company_id: int, po_id: int) -> PurchaseOrder:
    order = db.scalar(
        select(PurchaseOrder)
        .where(PurchaseOrder.id == po_id, PurchaseOrder.company_id == company_id)
        .options(selectinload(PurchaseOrder.lines))
    )
    if order is None:
        raise NotFoundError("采购订单不存在")
    return order


def _load_so(db: Session, company_id: int, so_id: int) -> SalesOrder:
    order = db.scalar(
        select(SalesOrder)
        .where(SalesOrder.id == so_id, SalesOrder.company_id == company_id)
        .options(selectinload(SalesOrder.lines))
    )
    if order is None:
        raise NotFoundError("销售订单不存在")
    return order


def list_purchase_orders(
    db: Session, company_id: int, *, page: int, page_size: int
) -> dict:
    """Paginated PO list (headers only, empty lines)."""
    total = db.scalar(
        select(func.count())
        .select_from(PurchaseOrder)
        .where(PurchaseOrder.company_id == company_id)
    ) or 0
    rows = db.scalars(
        select(PurchaseOrder)
        .where(PurchaseOrder.company_id == company_id)
        .options(selectinload(PurchaseOrder.lines))
        .order_by(PurchaseOrder.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return {"items": [_po_out(r) for r in rows], "meta": _page_meta(total, page, page_size)}


def create_purchase_order(
    db: Session, company_id: int, body: PurchaseOrderCreate, actor_id: int
) -> PurchaseOrderOut:
    """Create draft PO with lines and doc number."""
    _ensure_supplier(db, company_id, body.supplier_id)
    rate = Decimal(body.exchange_rate)
    doc_no = next_doc_no(db, company_id, "PO", actor_id)
    order = PurchaseOrder(
        company_id=company_id,
        doc_no=doc_no,
        supplier_id=body.supplier_id,
        status="draft",
        currency_code=body.currency_code.upper(),
        exchange_rate=rate,
        tax_rate=body.tax_rate,
        amount=Decimal("0"),
        base_amount=Decimal("0"),
        order_date=body.order_date,
        remark=body.remark,
        created_by=actor_id,
        updated_by=actor_id,
    )
    db.add(order)
    db.flush()

    total = Decimal("0")
    for idx, ln in enumerate(body.lines, start=1):
        _ensure_material(db, company_id, ln.material_id)
        amt = _money(ln.qty, ln.unit_price)
        base = (amt * rate).quantize(Decimal("0.01"))
        total += amt
        db.add(
            PurchaseOrderLine(
                company_id=company_id,
                po_id=order.id,
                line_no=idx,
                material_id=ln.material_id,
                qty=ln.qty,
                qty_received=Decimal("0"),
                unit_price=ln.unit_price,
                amount=amt,
                base_amount=base,
                created_by=actor_id,
                updated_by=actor_id,
            )
        )
    order.amount = total
    order.base_amount = (total * rate).quantize(Decimal("0.01"))
    db.commit()
    return _po_out(_load_po(db, company_id, order.id))


def get_purchase_order(db: Session, company_id: int, po_id: int) -> PurchaseOrderOut:
    return _po_out(_load_po(db, company_id, po_id))


def update_purchase_order(
    db: Session,
    company_id: int,
    po_id: int,
    body: PurchaseOrderUpdate,
    actor_id: int,
) -> PurchaseOrderOut:
    """Update draft PO only."""
    order = _load_po(db, company_id, po_id)
    if order.status != "draft":
        raise AppError("仅草稿可修改", code=40010)
    data = body.model_dump(exclude_unset=True)
    lines = data.pop("lines", None)
    if "supplier_id" in data:
        _ensure_supplier(db, company_id, data["supplier_id"])
    if "currency_code" in data and data["currency_code"]:
        data["currency_code"] = data["currency_code"].upper()
    for key, value in data.items():
        setattr(order, key, value)

    if lines is not None:
        for old in list(order.lines):
            db.delete(old)
        db.flush()
        rate = Decimal(order.exchange_rate)
        total = Decimal("0")
        for idx, ln in enumerate(lines, start=1):
            _ensure_material(db, company_id, ln["material_id"])
            qty = Decimal(str(ln["qty"]))
            price = Decimal(str(ln["unit_price"]))
            amt = _money(qty, price)
            total += amt
            db.add(
                PurchaseOrderLine(
                    company_id=company_id,
                    po_id=order.id,
                    line_no=idx,
                    material_id=ln["material_id"],
                    qty=qty,
                    qty_received=Decimal("0"),
                    unit_price=price,
                    amount=amt,
                    base_amount=(amt * rate).quantize(Decimal("0.01")),
                    created_by=actor_id,
                    updated_by=actor_id,
                )
            )
        order.amount = total
        order.base_amount = (total * rate).quantize(Decimal("0.01"))

    order.updated_by = actor_id
    db.commit()
    return _po_out(_load_po(db, company_id, order.id))


def confirm_purchase_order(
    db: Session, company_id: int, po_id: int, actor_id: int
) -> PurchaseOrderOut:
    order = _load_po(db, company_id, po_id)
    if order.status != "draft":
        raise AppError("仅草稿可确认", code=40010)
    if not order.lines:
        raise AppError("订单无明细", code=40010)
    order.status = "confirmed"
    order.updated_by = actor_id
    db.commit()
    return _po_out(_load_po(db, company_id, order.id))


def cancel_purchase_order(
    db: Session, company_id: int, po_id: int, actor_id: int
) -> PurchaseOrderOut:
    order = _load_po(db, company_id, po_id)
    if order.status not in ("draft", "confirmed"):
        raise AppError("当前状态不可取消", code=40010)
    if any(Decimal(ln.qty_received) > 0 for ln in order.lines):
        raise AppError("已发生入库，不可取消", code=40010)
    order.status = "cancelled"
    order.updated_by = actor_id
    db.commit()
    return _po_out(_load_po(db, company_id, order.id))


def list_stock_ins(
    db: Session, company_id: int, *, page: int, page_size: int
) -> dict:
    total = db.scalar(
        select(func.count())
        .select_from(StockInOrder)
        .where(StockInOrder.company_id == company_id)
    ) or 0
    rows = db.scalars(
        select(StockInOrder)
        .where(StockInOrder.company_id == company_id)
        .options(selectinload(StockInOrder.lines))
        .order_by(StockInOrder.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return {
        "items": [_stock_in_out(r) for r in rows],
        "meta": _page_meta(total, page, page_size),
    }


def create_stock_in(
    db: Session, company_id: int, body: StockInCreate, actor_id: int
) -> StockInOut:
    """Create draft stock-in against confirmed/partial PO."""
    _ensure_warehouse(db, company_id, body.warehouse_id)
    po = _load_po(db, company_id, body.po_id)
    if po.status not in ("confirmed", "partial"):
        raise AppError("采购订单状态不允许入库", code=40010)

    doc_no = next_doc_no(db, company_id, "IN", actor_id)
    order = StockInOrder(
        company_id=company_id,
        doc_no=doc_no,
        warehouse_id=body.warehouse_id,
        po_id=body.po_id,
        status="draft",
        remark=body.remark,
        created_by=actor_id,
        updated_by=actor_id,
    )
    db.add(order)
    db.flush()
    for idx, ln in enumerate(body.lines, start=1):
        _ensure_material(db, company_id, ln.material_id)
        db.add(
            StockInOrderLine(
                company_id=company_id,
                stock_in_id=order.id,
                line_no=idx,
                po_line_id=ln.po_line_id,
                material_id=ln.material_id,
                qty=ln.qty,
                created_by=actor_id,
                updated_by=actor_id,
            )
        )
    db.commit()
    return get_stock_in(db, company_id, order.id)


def get_stock_in(db: Session, company_id: int, stock_in_id: int) -> StockInOut:
    order = db.scalar(
        select(StockInOrder)
        .where(StockInOrder.id == stock_in_id, StockInOrder.company_id == company_id)
        .options(selectinload(StockInOrder.lines))
    )
    if order is None:
        raise NotFoundError("入库单不存在")
    return _stock_in_out(order)


def post_stock_in(
    db: Session, company_id: int, stock_in_id: int, actor_id: int
) -> StockInOut:
    """Post stock-in: increase inventory and update PO received qty."""
    order = db.scalar(
        select(StockInOrder)
        .where(StockInOrder.id == stock_in_id, StockInOrder.company_id == company_id)
        .options(selectinload(StockInOrder.lines))
        .with_for_update()
    )
    if order is None:
        raise NotFoundError("入库单不存在")
    if order.status != "draft":
        raise AppError("仅草稿可过账", code=40010)

    po = _load_po(db, company_id, order.po_id)
    if po.status not in ("confirmed", "partial"):
        raise AppError("采购订单状态不允许入库过账", code=40010)

    try:
        for ln in order.lines:
            inv_services.increase(
                db,
                company_id=company_id,
                warehouse_id=order.warehouse_id,
                material_id=ln.material_id,
                qty=Decimal(ln.qty),
                actor_id=actor_id,
                tx_type="in",
                ref_doc_type="stock_in",
                ref_doc_id=order.id,
                ref_doc_no=order.doc_no,
            )
            if ln.po_line_id:
                po_line = next((x for x in po.lines if x.id == ln.po_line_id), None)
                if po_line is None or po_line.company_id != company_id:
                    raise AppError("采购行不存在", code=40010)
                po_line.qty_received = Decimal(po_line.qty_received) + Decimal(ln.qty)
                if Decimal(po_line.qty_received) > Decimal(po_line.qty):
                    raise AppError("入库数量超过采购数量", code=40010)
                po_line.updated_by = actor_id

        # Refresh PO status from lines
        all_done = all(Decimal(x.qty_received) >= Decimal(x.qty) for x in po.lines)
        any_recv = any(Decimal(x.qty_received) > 0 for x in po.lines)
        if all_done:
            po.status = "completed"
        elif any_recv:
            po.status = "partial"
        po.updated_by = actor_id

        order.status = "posted"
        order.posted_at = datetime.now(timezone.utc).replace(tzinfo=None)
        order.updated_by = actor_id
        db.flush()

        if after_stock_in_posted is not None:
            after_stock_in_posted(db, company_id, order, actor_id)

        db.commit()
    except AppError:
        db.rollback()
        raise

    return get_stock_in(db, company_id, stock_in_id)


def list_sales_orders(
    db: Session, company_id: int, *, page: int, page_size: int
) -> dict:
    total = db.scalar(
        select(func.count())
        .select_from(SalesOrder)
        .where(SalesOrder.company_id == company_id)
    ) or 0
    rows = db.scalars(
        select(SalesOrder)
        .where(SalesOrder.company_id == company_id)
        .options(selectinload(SalesOrder.lines))
        .order_by(SalesOrder.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return {"items": [_so_out(r) for r in rows], "meta": _page_meta(total, page, page_size)}


def create_sales_order(
    db: Session, company_id: int, body: SalesOrderCreate, actor_id: int
) -> SalesOrderOut:
    _ensure_customer(db, company_id, body.customer_id)
    rate = Decimal(body.exchange_rate)
    doc_no = next_doc_no(db, company_id, "SO", actor_id)
    order = SalesOrder(
        company_id=company_id,
        doc_no=doc_no,
        customer_id=body.customer_id,
        status="draft",
        currency_code=body.currency_code.upper(),
        exchange_rate=rate,
        tax_rate=body.tax_rate,
        amount=Decimal("0"),
        base_amount=Decimal("0"),
        order_date=body.order_date,
        remark=body.remark,
        created_by=actor_id,
        updated_by=actor_id,
    )
    db.add(order)
    db.flush()
    total = Decimal("0")
    for idx, ln in enumerate(body.lines, start=1):
        _ensure_material(db, company_id, ln.material_id)
        amt = _money(ln.qty, ln.unit_price)
        total += amt
        db.add(
            SalesOrderLine(
                company_id=company_id,
                so_id=order.id,
                line_no=idx,
                material_id=ln.material_id,
                qty=ln.qty,
                qty_shipped=Decimal("0"),
                unit_price=ln.unit_price,
                amount=amt,
                base_amount=(amt * rate).quantize(Decimal("0.01")),
                created_by=actor_id,
                updated_by=actor_id,
            )
        )
    order.amount = total
    order.base_amount = (total * rate).quantize(Decimal("0.01"))
    db.commit()
    return _so_out(_load_so(db, company_id, order.id))


def get_sales_order(db: Session, company_id: int, so_id: int) -> SalesOrderOut:
    return _so_out(_load_so(db, company_id, so_id))


def update_sales_order(
    db: Session,
    company_id: int,
    so_id: int,
    body: SalesOrderUpdate,
    actor_id: int,
) -> SalesOrderOut:
    order = _load_so(db, company_id, so_id)
    if order.status != "draft":
        raise AppError("仅草稿可修改", code=40010)
    data = body.model_dump(exclude_unset=True)
    lines = data.pop("lines", None)
    if "customer_id" in data:
        _ensure_customer(db, company_id, data["customer_id"])
    if "currency_code" in data and data["currency_code"]:
        data["currency_code"] = data["currency_code"].upper()
    for key, value in data.items():
        setattr(order, key, value)
    if lines is not None:
        for old in list(order.lines):
            db.delete(old)
        db.flush()
        rate = Decimal(order.exchange_rate)
        total = Decimal("0")
        for idx, ln in enumerate(lines, start=1):
            _ensure_material(db, company_id, ln["material_id"])
            qty = Decimal(str(ln["qty"]))
            price = Decimal(str(ln["unit_price"]))
            amt = _money(qty, price)
            total += amt
            db.add(
                SalesOrderLine(
                    company_id=company_id,
                    so_id=order.id,
                    line_no=idx,
                    material_id=ln["material_id"],
                    qty=qty,
                    qty_shipped=Decimal("0"),
                    unit_price=price,
                    amount=amt,
                    base_amount=(amt * rate).quantize(Decimal("0.01")),
                    created_by=actor_id,
                    updated_by=actor_id,
                )
            )
        order.amount = total
        order.base_amount = (total * rate).quantize(Decimal("0.01"))
    order.updated_by = actor_id
    db.commit()
    return _so_out(_load_so(db, company_id, order.id))


def confirm_sales_order(
    db: Session, company_id: int, so_id: int, actor_id: int
) -> SalesOrderOut:
    order = _load_so(db, company_id, so_id)
    if order.status != "draft":
        raise AppError("仅草稿可确认", code=40010)
    if not order.lines:
        raise AppError("订单无明细", code=40010)
    order.status = "confirmed"
    order.updated_by = actor_id
    db.commit()
    return _so_out(_load_so(db, company_id, order.id))


def cancel_sales_order(
    db: Session, company_id: int, so_id: int, actor_id: int
) -> SalesOrderOut:
    order = _load_so(db, company_id, so_id)
    if order.status not in ("draft", "confirmed"):
        raise AppError("当前状态不可取消", code=40010)
    if any(Decimal(ln.qty_shipped) > 0 for ln in order.lines):
        raise AppError("已发生出库，不可取消", code=40010)
    order.status = "cancelled"
    order.updated_by = actor_id
    db.commit()
    return _so_out(_load_so(db, company_id, order.id))


def list_stock_outs(
    db: Session, company_id: int, *, page: int, page_size: int
) -> dict:
    total = db.scalar(
        select(func.count())
        .select_from(StockOutOrder)
        .where(StockOutOrder.company_id == company_id)
    ) or 0
    rows = db.scalars(
        select(StockOutOrder)
        .where(StockOutOrder.company_id == company_id)
        .options(selectinload(StockOutOrder.lines))
        .order_by(StockOutOrder.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return {
        "items": [_stock_out_out(r) for r in rows],
        "meta": _page_meta(total, page, page_size),
    }


def create_stock_out(
    db: Session, company_id: int, body: StockOutCreate, actor_id: int
) -> StockOutOut:
    _ensure_warehouse(db, company_id, body.warehouse_id)
    so = _load_so(db, company_id, body.so_id)
    if so.status not in ("confirmed", "partial"):
        raise AppError("销售订单状态不允许出库", code=40010)

    doc_no = next_doc_no(db, company_id, "OUT", actor_id)
    order = StockOutOrder(
        company_id=company_id,
        doc_no=doc_no,
        warehouse_id=body.warehouse_id,
        so_id=body.so_id,
        status="draft",
        remark=body.remark,
        created_by=actor_id,
        updated_by=actor_id,
    )
    db.add(order)
    db.flush()
    for idx, ln in enumerate(body.lines, start=1):
        _ensure_material(db, company_id, ln.material_id)
        db.add(
            StockOutOrderLine(
                company_id=company_id,
                stock_out_id=order.id,
                line_no=idx,
                so_line_id=ln.so_line_id,
                material_id=ln.material_id,
                qty=ln.qty,
                created_by=actor_id,
                updated_by=actor_id,
            )
        )
    db.commit()
    return get_stock_out(db, company_id, order.id)


def get_stock_out(db: Session, company_id: int, stock_out_id: int) -> StockOutOut:
    order = db.scalar(
        select(StockOutOrder)
        .where(StockOutOrder.id == stock_out_id, StockOutOrder.company_id == company_id)
        .options(selectinload(StockOutOrder.lines))
    )
    if order is None:
        raise NotFoundError("出库单不存在")
    return _stock_out_out(order)


def post_stock_out(
    db: Session, company_id: int, stock_out_id: int, actor_id: int
) -> StockOutOut:
    """Post stock-out: decrease inventory and update SO shipped qty."""
    order = db.scalar(
        select(StockOutOrder)
        .where(StockOutOrder.id == stock_out_id, StockOutOrder.company_id == company_id)
        .options(selectinload(StockOutOrder.lines))
        .with_for_update()
    )
    if order is None:
        raise NotFoundError("出库单不存在")
    if order.status != "draft":
        raise AppError("仅草稿可过账", code=40010)

    so = _load_so(db, company_id, order.so_id)
    if so.status not in ("confirmed", "partial"):
        raise AppError("销售订单状态不允许出库过账", code=40010)

    try:
        for ln in order.lines:
            inv_services.decrease(
                db,
                company_id=company_id,
                warehouse_id=order.warehouse_id,
                material_id=ln.material_id,
                qty=Decimal(ln.qty),
                actor_id=actor_id,
                tx_type="out",
                ref_doc_type="stock_out",
                ref_doc_id=order.id,
                ref_doc_no=order.doc_no,
            )
            if ln.so_line_id:
                so_line = next((x for x in so.lines if x.id == ln.so_line_id), None)
                if so_line is None or so_line.company_id != company_id:
                    raise AppError("销售行不存在", code=40010)
                so_line.qty_shipped = Decimal(so_line.qty_shipped) + Decimal(ln.qty)
                if Decimal(so_line.qty_shipped) > Decimal(so_line.qty):
                    raise AppError("出库数量超过销售数量", code=40010)
                so_line.updated_by = actor_id

        all_done = all(Decimal(x.qty_shipped) >= Decimal(x.qty) for x in so.lines)
        any_ship = any(Decimal(x.qty_shipped) > 0 for x in so.lines)
        if all_done:
            so.status = "completed"
        elif any_ship:
            so.status = "partial"
        so.updated_by = actor_id

        order.status = "posted"
        order.posted_at = datetime.now(timezone.utc).replace(tzinfo=None)
        order.updated_by = actor_id
        db.flush()

        if after_stock_out_posted is not None:
            after_stock_out_posted(db, company_id, order, actor_id)

        db.commit()
    except AppError:
        db.rollback()
        raise

    return get_stock_out(db, company_id, stock_out_id)
