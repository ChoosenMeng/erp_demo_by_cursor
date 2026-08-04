"""M3 purchase, sales, and stock document ORM models."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.mysql import DATETIME
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.shared.mixins import AuditMixin


class DocumentSequence(AuditMixin, Base):
    """Per-company document number sequence."""

    __tablename__ = "document_sequences"
    __table_args__ = (
        UniqueConstraint("company_id", "doc_type", name="uq_document_sequences_company_type"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("companies.id"), nullable=False)
    doc_type: Mapped[str] = mapped_column(String(32), nullable=False)
    prefix: Mapped[str] = mapped_column(String(16), nullable=False)
    next_value: Mapped[int] = mapped_column(BigInteger, nullable=False, default=1)
    reset_rule: Mapped[str] = mapped_column(String(16), nullable=False, default="never")


class PurchaseOrder(AuditMixin, Base):
    """Purchase order header."""

    __tablename__ = "purchase_orders"
    __table_args__ = (UniqueConstraint("company_id", "doc_no", name="uq_purchase_orders_company_no"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("companies.id"), nullable=False)
    doc_no: Mapped[str] = mapped_column(String(64), nullable=False)
    supplier_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("suppliers.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, default="CNY")
    exchange_rate: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False, default=1)
    tax_rate: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=0)
    base_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=0)
    order_date: Mapped[date] = mapped_column(Date, nullable=False)
    remark: Mapped[str | None] = mapped_column(String(255), nullable=True)

    lines: Mapped[list["PurchaseOrderLine"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )


class PurchaseOrderLine(AuditMixin, Base):
    """Purchase order line."""

    __tablename__ = "purchase_order_lines"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("companies.id"), nullable=False)
    po_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("purchase_orders.id"), nullable=False)
    line_no: Mapped[int] = mapped_column(Integer, nullable=False)
    material_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("materials.id"), nullable=False)
    qty: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    qty_received: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    base_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)

    order: Mapped[PurchaseOrder] = relationship(back_populates="lines")


class StockInOrder(AuditMixin, Base):
    """Inbound stock document header."""

    __tablename__ = "stock_in_orders"
    __table_args__ = (UniqueConstraint("company_id", "doc_no", name="uq_stock_in_orders_company_no"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("companies.id"), nullable=False)
    doc_no: Mapped[str] = mapped_column(String(64), nullable=False)
    warehouse_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("warehouses.id"), nullable=False)
    po_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("purchase_orders.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    posted_at: Mapped[datetime | None] = mapped_column(DATETIME(fsp=6), nullable=True)
    remark: Mapped[str | None] = mapped_column(String(255), nullable=True)

    lines: Mapped[list["StockInOrderLine"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )


class StockInOrderLine(AuditMixin, Base):
    """Inbound stock document line."""

    __tablename__ = "stock_in_order_lines"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("companies.id"), nullable=False)
    stock_in_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("stock_in_orders.id"), nullable=False
    )
    line_no: Mapped[int] = mapped_column(Integer, nullable=False)
    po_line_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("purchase_order_lines.id"), nullable=True
    )
    material_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("materials.id"), nullable=False)
    qty: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)

    order: Mapped[StockInOrder] = relationship(back_populates="lines")


class SalesOrder(AuditMixin, Base):
    """Sales order header."""

    __tablename__ = "sales_orders"
    __table_args__ = (UniqueConstraint("company_id", "doc_no", name="uq_sales_orders_company_no"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("companies.id"), nullable=False)
    doc_no: Mapped[str] = mapped_column(String(64), nullable=False)
    customer_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("customers.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, default="CNY")
    exchange_rate: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False, default=1)
    tax_rate: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=0)
    base_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=0)
    order_date: Mapped[date] = mapped_column(Date, nullable=False)
    remark: Mapped[str | None] = mapped_column(String(255), nullable=True)

    lines: Mapped[list["SalesOrderLine"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )


class SalesOrderLine(AuditMixin, Base):
    """Sales order line."""

    __tablename__ = "sales_order_lines"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("companies.id"), nullable=False)
    so_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("sales_orders.id"), nullable=False)
    line_no: Mapped[int] = mapped_column(Integer, nullable=False)
    material_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("materials.id"), nullable=False)
    qty: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    qty_shipped: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    base_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)

    order: Mapped[SalesOrder] = relationship(back_populates="lines")


class StockOutOrder(AuditMixin, Base):
    """Outbound stock document header."""

    __tablename__ = "stock_out_orders"
    __table_args__ = (
        UniqueConstraint("company_id", "doc_no", name="uq_stock_out_orders_company_no"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("companies.id"), nullable=False)
    doc_no: Mapped[str] = mapped_column(String(64), nullable=False)
    warehouse_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("warehouses.id"), nullable=False)
    so_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("sales_orders.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    posted_at: Mapped[datetime | None] = mapped_column(DATETIME(fsp=6), nullable=True)
    remark: Mapped[str | None] = mapped_column(String(255), nullable=True)

    lines: Mapped[list["StockOutOrderLine"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )


class StockOutOrderLine(AuditMixin, Base):
    """Outbound stock document line."""

    __tablename__ = "stock_out_order_lines"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("companies.id"), nullable=False)
    stock_out_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("stock_out_orders.id"), nullable=False
    )
    line_no: Mapped[int] = mapped_column(Integer, nullable=False)
    so_line_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("sales_order_lines.id"), nullable=True
    )
    material_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("materials.id"), nullable=False)
    qty: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)

    order: Mapped[StockOutOrder] = relationship(back_populates="lines")
