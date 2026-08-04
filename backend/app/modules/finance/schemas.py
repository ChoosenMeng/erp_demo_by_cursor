"""Finance and dashboard schemas."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class ApBillOut(BaseModel):
    """AP bill response."""

    id: int
    company_id: int
    doc_no: str
    supplier_id: int
    supplier_name: str | None = None
    source_type: str
    source_id: int
    currency_code: str
    exchange_rate: Decimal
    amount: Decimal
    base_amount: Decimal
    paid_amount: Decimal
    status: str
    bill_date: date


class ArBillOut(BaseModel):
    """AR bill response."""

    id: int
    company_id: int
    doc_no: str
    customer_id: int
    customer_name: str | None = None
    source_type: str
    source_id: int
    currency_code: str
    exchange_rate: Decimal
    amount: Decimal
    base_amount: Decimal
    received_amount: Decimal
    status: str
    bill_date: date


class PaymentCreate(BaseModel):
    """Register AP payment."""

    amount: Decimal = Field(gt=0)
    pay_date: date
    remark: str | None = Field(default=None, max_length=255)


class ReceiptCreate(BaseModel):
    """Register AR receipt."""

    amount: Decimal = Field(gt=0)
    pay_date: date
    remark: str | None = Field(default=None, max_length=255)


class PaymentOut(BaseModel):
    """Payment record response."""

    id: int
    ap_bill_id: int
    amount: Decimal
    base_amount: Decimal
    currency_code: str
    pay_date: date
    status: str
    remark: str | None


class ReceiptOut(BaseModel):
    """Receipt record response."""

    id: int
    ar_bill_id: int
    amount: Decimal
    base_amount: Decimal
    currency_code: str
    pay_date: date
    status: str
    remark: str | None


class PaymentResult(BaseModel):
    """Payment + updated bill."""

    payment: PaymentOut
    bill: ApBillOut


class ReceiptResult(BaseModel):
    """Receipt + updated bill."""

    receipt: ReceiptOut
    bill: ArBillOut


class DashboardSummary(BaseModel):
    """Dashboard KPI summary."""

    sales_amount_today: Decimal
    sales_amount_month: Decimal
    purchase_amount_month: Decimal
    inventory_sku_count: int
    pending_so_count: int
    pending_po_count: int


class TrendPoint(BaseModel):
    """Sales trend point."""

    date: date
    amount: Decimal


class SalesTrend(BaseModel):
    """Sales trend series."""

    points: list[TrendPoint]
