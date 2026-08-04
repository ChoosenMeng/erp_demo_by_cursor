"""Pydantic schemas for purchase / sales / stock documents."""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.modules.org.schemas import PageMeta


class OrderLineIn(BaseModel):
    """Create/update order line input."""

    material_id: int
    qty: Decimal = Field(gt=0)
    unit_price: Decimal = Field(ge=0)


class PurchaseOrderCreate(BaseModel):
    """Create PO payload."""

    supplier_id: int
    order_date: date
    currency_code: str = Field(default="CNY", min_length=3, max_length=3)
    tax_rate: Decimal | None = None
    remark: str | None = Field(default=None, max_length=255)
    lines: list[OrderLineIn] = Field(min_length=1)


class PurchaseOrderUpdate(BaseModel):
    """Patch draft PO."""

    supplier_id: int | None = None
    order_date: date | None = None
    currency_code: str | None = Field(default=None, min_length=3, max_length=3)
    tax_rate: Decimal | None = None
    remark: str | None = Field(default=None, max_length=255)
    lines: list[OrderLineIn] | None = None


class PurchaseOrderLineOut(BaseModel):
    """PO line response."""

    id: int
    line_no: int
    material_id: int
    qty: Decimal
    qty_received: Decimal
    unit_price: Decimal
    amount: Decimal
    base_amount: Decimal


class PurchaseOrderOut(BaseModel):
    """PO header + lines."""

    id: int
    company_id: int
    doc_no: str
    supplier_id: int
    status: str
    currency_code: str
    exchange_rate: Decimal
    tax_rate: Decimal | None
    amount: Decimal
    base_amount: Decimal
    order_date: date
    remark: str | None
    lines: list[PurchaseOrderLineOut]


class StockInLineIn(BaseModel):
    """Stock-in line input."""

    po_line_id: int | None = None
    material_id: int
    qty: Decimal = Field(gt=0)


class StockInCreate(BaseModel):
    """Create stock-in draft."""

    warehouse_id: int
    po_id: int
    remark: str | None = Field(default=None, max_length=255)
    lines: list[StockInLineIn] = Field(min_length=1)


class StockInLineOut(BaseModel):
    """Stock-in line response."""

    id: int
    line_no: int
    po_line_id: int | None
    material_id: int
    qty: Decimal


class StockInOut(BaseModel):
    """Stock-in header + lines."""

    id: int
    company_id: int
    doc_no: str
    warehouse_id: int
    po_id: int
    status: str
    posted_at: datetime | None
    remark: str | None
    lines: list[StockInLineOut]


class SalesOrderCreate(BaseModel):
    """Create SO payload."""

    customer_id: int
    order_date: date
    currency_code: str = Field(default="CNY", min_length=3, max_length=3)
    tax_rate: Decimal | None = None
    remark: str | None = Field(default=None, max_length=255)
    lines: list[OrderLineIn] = Field(min_length=1)


class SalesOrderUpdate(BaseModel):
    """Patch draft SO."""

    customer_id: int | None = None
    order_date: date | None = None
    currency_code: str | None = Field(default=None, min_length=3, max_length=3)
    tax_rate: Decimal | None = None
    remark: str | None = Field(default=None, max_length=255)
    lines: list[OrderLineIn] | None = None


class SalesOrderLineOut(BaseModel):
    """SO line response."""

    id: int
    line_no: int
    material_id: int
    qty: Decimal
    qty_shipped: Decimal
    unit_price: Decimal
    amount: Decimal
    base_amount: Decimal


class SalesOrderOut(BaseModel):
    """SO header + lines."""

    id: int
    company_id: int
    doc_no: str
    customer_id: int
    status: str
    currency_code: str
    exchange_rate: Decimal
    tax_rate: Decimal | None
    amount: Decimal
    base_amount: Decimal
    order_date: date
    remark: str | None
    lines: list[SalesOrderLineOut]


class StockOutLineIn(BaseModel):
    """Stock-out line input."""

    so_line_id: int | None = None
    material_id: int
    qty: Decimal = Field(gt=0)


class StockOutCreate(BaseModel):
    """Create stock-out draft."""

    warehouse_id: int
    so_id: int
    remark: str | None = Field(default=None, max_length=255)
    lines: list[StockOutLineIn] = Field(min_length=1)


class StockOutLineOut(BaseModel):
    """Stock-out line response."""

    id: int
    line_no: int
    so_line_id: int | None
    material_id: int
    qty: Decimal


class StockOutOut(BaseModel):
    """Stock-out header + lines."""

    id: int
    company_id: int
    doc_no: str
    warehouse_id: int
    so_id: int
    status: str
    posted_at: datetime | None
    remark: str | None
    lines: list[StockOutLineOut]


__all__ = [
    "PageMeta",
    "OrderLineIn",
    "PurchaseOrderCreate",
    "PurchaseOrderUpdate",
    "PurchaseOrderOut",
    "StockInCreate",
    "StockInOut",
    "SalesOrderCreate",
    "SalesOrderUpdate",
    "SalesOrderOut",
    "StockOutCreate",
    "StockOutOut",
]
