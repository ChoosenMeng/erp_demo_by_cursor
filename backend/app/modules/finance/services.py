"""AP/AR generation, payments, and dashboard aggregations."""

from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import AppError, NotFoundError
from app.modules.finance.models import ApBill, ArBill, PaymentRecord, ReceiptRecord
from app.modules.finance.schemas import (
    ApBillOut,
    ArBillOut,
    DashboardSummary,
    PaymentCreate,
    PaymentOut,
    PaymentResult,
    ReceiptCreate,
    ReceiptOut,
    ReceiptResult,
    SalesTrend,
    TrendPoint,
)
from app.modules.inventory.models import InventoryBalance
from app.modules.master.models import Customer, Supplier
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
from app.modules.trade.sequences import next_doc_no


def _page_meta(total: int, page: int, page_size: int) -> PageMeta:
    return PageMeta(page=page, page_size=page_size, total=total)


def _ap_out(db: Session, bill: ApBill) -> ApBillOut:
    supplier = db.get(Supplier, bill.supplier_id)
    return ApBillOut(
        id=bill.id,
        company_id=bill.company_id,
        doc_no=bill.doc_no,
        supplier_id=bill.supplier_id,
        supplier_name=supplier.name if supplier else None,
        source_type=bill.source_type,
        source_id=bill.source_id,
        currency_code=bill.currency_code,
        exchange_rate=bill.exchange_rate,
        amount=bill.amount,
        base_amount=bill.base_amount,
        paid_amount=bill.paid_amount,
        status=bill.status,
        bill_date=bill.bill_date,
    )


def _ar_out(db: Session, bill: ArBill) -> ArBillOut:
    customer = db.get(Customer, bill.customer_id)
    return ArBillOut(
        id=bill.id,
        company_id=bill.company_id,
        doc_no=bill.doc_no,
        customer_id=bill.customer_id,
        customer_name=customer.name if customer else None,
        source_type=bill.source_type,
        source_id=bill.source_id,
        currency_code=bill.currency_code,
        exchange_rate=bill.exchange_rate,
        amount=bill.amount,
        base_amount=bill.base_amount,
        received_amount=bill.received_amount,
        status=bill.status,
        bill_date=bill.bill_date,
    )


def create_ap_from_stock_in(
    db: Session, company_id: int, stock_in: StockInOrder, actor_id: int
) -> ApBill:
    """Create AP bill after stock-in posting (idempotent by source)."""
    exists = db.scalar(
        select(ApBill.id).where(
            ApBill.company_id == company_id,
            ApBill.source_type == "stock_in",
            ApBill.source_id == stock_in.id,
        )
    )
    if exists:
        return db.get(ApBill, exists)  # type: ignore[return-value]

    po = db.get(PurchaseOrder, stock_in.po_id)
    if po is None or po.company_id != company_id:
        raise AppError("关联采购订单不存在", code=40020)

    lines = db.scalars(
        select(StockInOrderLine).where(StockInOrderLine.stock_in_id == stock_in.id)
    ).all()
    amount = Decimal("0")
    for ln in lines:
        unit = Decimal("0")
        if ln.po_line_id:
            po_line = db.get(PurchaseOrderLine, ln.po_line_id)
            if po_line:
                unit = Decimal(po_line.unit_price)
        amount += (Decimal(ln.qty) * unit).quantize(Decimal("0.01"))

    rate = Decimal(po.exchange_rate)
    bill = ApBill(
        company_id=company_id,
        doc_no=next_doc_no(db, company_id, "AP", actor_id),
        supplier_id=po.supplier_id,
        source_type="stock_in",
        source_id=stock_in.id,
        currency_code=po.currency_code,
        exchange_rate=rate,
        amount=amount,
        base_amount=(amount * rate).quantize(Decimal("0.01")),
        paid_amount=Decimal("0"),
        status="open",
        bill_date=date.today(),
        created_by=actor_id,
        updated_by=actor_id,
    )
    db.add(bill)
    db.flush()
    return bill


def create_ar_from_stock_out(
    db: Session, company_id: int, stock_out: StockOutOrder, actor_id: int
) -> ArBill:
    """Create AR bill after stock-out posting (idempotent by source)."""
    exists = db.scalar(
        select(ArBill.id).where(
            ArBill.company_id == company_id,
            ArBill.source_type == "stock_out",
            ArBill.source_id == stock_out.id,
        )
    )
    if exists:
        return db.get(ArBill, exists)  # type: ignore[return-value]

    so = db.get(SalesOrder, stock_out.so_id)
    if so is None or so.company_id != company_id:
        raise AppError("关联销售订单不存在", code=40020)

    lines = db.scalars(
        select(StockOutOrderLine).where(StockOutOrderLine.stock_out_id == stock_out.id)
    ).all()
    amount = Decimal("0")
    for ln in lines:
        unit = Decimal("0")
        if ln.so_line_id:
            so_line = db.get(SalesOrderLine, ln.so_line_id)
            if so_line:
                unit = Decimal(so_line.unit_price)
        amount += (Decimal(ln.qty) * unit).quantize(Decimal("0.01"))

    rate = Decimal(so.exchange_rate)
    bill = ArBill(
        company_id=company_id,
        doc_no=next_doc_no(db, company_id, "AR", actor_id),
        customer_id=so.customer_id,
        source_type="stock_out",
        source_id=stock_out.id,
        currency_code=so.currency_code,
        exchange_rate=rate,
        amount=amount,
        base_amount=(amount * rate).quantize(Decimal("0.01")),
        received_amount=Decimal("0"),
        status="open",
        bill_date=date.today(),
        created_by=actor_id,
        updated_by=actor_id,
    )
    db.add(bill)
    db.flush()
    return bill


def list_ap_bills(
    db: Session,
    company_id: int,
    *,
    status: str | None,
    page: int,
    page_size: int,
) -> dict:
    filters = [ApBill.company_id == company_id]
    if status:
        filters.append(ApBill.status == status)
    total = db.scalar(select(func.count()).select_from(ApBill).where(*filters)) or 0
    rows = db.scalars(
        select(ApBill)
        .where(*filters)
        .order_by(ApBill.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return {
        "items": [_ap_out(db, r) for r in rows],
        "meta": _page_meta(total, page, page_size),
    }


def get_ap_bill(db: Session, company_id: int, bill_id: int) -> ApBillOut:
    bill = db.get(ApBill, bill_id)
    if bill is None or bill.company_id != company_id:
        raise NotFoundError("应付单不存在")
    return _ap_out(db, bill)


def register_payment(
    db: Session, company_id: int, bill_id: int, body: PaymentCreate, actor_id: int
) -> PaymentResult:
    """Post payment against AP; reject overpay."""
    bill = db.get(ApBill, bill_id)
    if bill is None or bill.company_id != company_id:
        raise NotFoundError("应付单不存在")
    if bill.status in ("paid", "void"):
        raise AppError("应付单状态不允许付款", code=40021)

    remaining = Decimal(bill.amount) - Decimal(bill.paid_amount)
    if body.amount > remaining:
        raise AppError("付款金额超过未付余额", code=40022)

    rate = Decimal(bill.exchange_rate)
    payment = PaymentRecord(
        company_id=company_id,
        ap_bill_id=bill.id,
        amount=body.amount,
        base_amount=(body.amount * rate).quantize(Decimal("0.01")),
        currency_code=bill.currency_code,
        exchange_rate=rate,
        pay_date=body.pay_date,
        status="posted",
        remark=body.remark,
        created_by=actor_id,
        updated_by=actor_id,
    )
    db.add(payment)
    bill.paid_amount = Decimal(bill.paid_amount) + body.amount
    if bill.paid_amount >= bill.amount:
        bill.status = "paid"
    else:
        bill.status = "partial"
    bill.updated_by = actor_id
    db.commit()
    db.refresh(payment)
    db.refresh(bill)
    return PaymentResult(
        payment=PaymentOut(
            id=payment.id,
            ap_bill_id=payment.ap_bill_id,
            amount=payment.amount,
            base_amount=payment.base_amount,
            currency_code=payment.currency_code,
            pay_date=payment.pay_date,
            status=payment.status,
            remark=payment.remark,
        ),
        bill=_ap_out(db, bill),
    )


def list_ar_bills(
    db: Session,
    company_id: int,
    *,
    status: str | None,
    page: int,
    page_size: int,
) -> dict:
    filters = [ArBill.company_id == company_id]
    if status:
        filters.append(ArBill.status == status)
    total = db.scalar(select(func.count()).select_from(ArBill).where(*filters)) or 0
    rows = db.scalars(
        select(ArBill)
        .where(*filters)
        .order_by(ArBill.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return {
        "items": [_ar_out(db, r) for r in rows],
        "meta": _page_meta(total, page, page_size),
    }


def get_ar_bill(db: Session, company_id: int, bill_id: int) -> ArBillOut:
    bill = db.get(ArBill, bill_id)
    if bill is None or bill.company_id != company_id:
        raise NotFoundError("应收单不存在")
    return _ar_out(db, bill)


def register_receipt(
    db: Session, company_id: int, bill_id: int, body: ReceiptCreate, actor_id: int
) -> ReceiptResult:
    """Post receipt against AR; reject over-receive."""
    bill = db.get(ArBill, bill_id)
    if bill is None or bill.company_id != company_id:
        raise NotFoundError("应收单不存在")
    if bill.status in ("paid", "void"):
        raise AppError("应收单状态不允许收款", code=40021)

    remaining = Decimal(bill.amount) - Decimal(bill.received_amount)
    if body.amount > remaining:
        raise AppError("收款金额超过未收余额", code=40022)

    rate = Decimal(bill.exchange_rate)
    receipt = ReceiptRecord(
        company_id=company_id,
        ar_bill_id=bill.id,
        amount=body.amount,
        base_amount=(body.amount * rate).quantize(Decimal("0.01")),
        currency_code=bill.currency_code,
        exchange_rate=rate,
        pay_date=body.pay_date,
        status="posted",
        remark=body.remark,
        created_by=actor_id,
        updated_by=actor_id,
    )
    db.add(receipt)
    bill.received_amount = Decimal(bill.received_amount) + body.amount
    if bill.received_amount >= bill.amount:
        bill.status = "paid"
    else:
        bill.status = "partial"
    bill.updated_by = actor_id
    db.commit()
    db.refresh(receipt)
    db.refresh(bill)
    return ReceiptResult(
        receipt=ReceiptOut(
            id=receipt.id,
            ar_bill_id=receipt.ar_bill_id,
            amount=receipt.amount,
            base_amount=receipt.base_amount,
            currency_code=receipt.currency_code,
            pay_date=receipt.pay_date,
            status=receipt.status,
            remark=receipt.remark,
        ),
        bill=_ar_out(db, bill),
    )


def dashboard_summary(db: Session, company_id: int) -> DashboardSummary:
    """Aggregate KPIs for active company."""
    today = date.today()
    month_start = today.replace(day=1)

    sales_today = db.scalar(
        select(func.coalesce(func.sum(SalesOrder.base_amount), 0)).where(
            SalesOrder.company_id == company_id,
            SalesOrder.order_date == today,
            SalesOrder.status.notin_(["draft", "cancelled"]),
        )
    )
    sales_month = db.scalar(
        select(func.coalesce(func.sum(SalesOrder.base_amount), 0)).where(
            SalesOrder.company_id == company_id,
            SalesOrder.order_date >= month_start,
            SalesOrder.status.notin_(["draft", "cancelled"]),
        )
    )
    purchase_month = db.scalar(
        select(func.coalesce(func.sum(PurchaseOrder.base_amount), 0)).where(
            PurchaseOrder.company_id == company_id,
            PurchaseOrder.order_date >= month_start,
            PurchaseOrder.status.notin_(["draft", "cancelled"]),
        )
    )
    sku_count = db.scalar(
        select(func.count()).select_from(InventoryBalance).where(
            InventoryBalance.company_id == company_id,
            InventoryBalance.qty_on_hand > 0,
        )
    ) or 0
    pending_so = db.scalar(
        select(func.count()).select_from(SalesOrder).where(
            SalesOrder.company_id == company_id,
            SalesOrder.status.in_(["confirmed", "partial"]),
        )
    ) or 0
    pending_po = db.scalar(
        select(func.count()).select_from(PurchaseOrder).where(
            PurchaseOrder.company_id == company_id,
            PurchaseOrder.status.in_(["confirmed", "partial"]),
        )
    ) or 0

    return DashboardSummary(
        sales_amount_today=Decimal(sales_today),
        sales_amount_month=Decimal(sales_month),
        purchase_amount_month=Decimal(purchase_month),
        inventory_sku_count=int(sku_count),
        pending_so_count=int(pending_so),
        pending_po_count=int(pending_po),
    )


def sales_trend(db: Session, company_id: int, days: int) -> SalesTrend:
    """Daily sales amounts for last N days (including today)."""
    days = max(1, min(days, 90))
    end = date.today()
    start = end - timedelta(days=days - 1)
    rows = db.execute(
        select(SalesOrder.order_date, func.coalesce(func.sum(SalesOrder.base_amount), 0))
        .where(
            SalesOrder.company_id == company_id,
            SalesOrder.order_date >= start,
            SalesOrder.order_date <= end,
            SalesOrder.status.notin_(["draft", "cancelled"]),
        )
        .group_by(SalesOrder.order_date)
    ).all()
    by_day = {d: Decimal(amt) for d, amt in rows}
    points = [
        TrendPoint(date=start + timedelta(days=i), amount=by_day.get(start + timedelta(days=i), Decimal("0")))
        for i in range(days)
    ]
    return SalesTrend(points=points)
