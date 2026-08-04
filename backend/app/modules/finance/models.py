"""M4 AP/AR and payment/receipt ORM models."""

from datetime import date
from decimal import Decimal

from sqlalchemy import BigInteger, Date, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.shared.mixins import AuditMixin


class ApBill(AuditMixin, Base):
    """Accounts payable bill."""

    __tablename__ = "ap_bills"
    __table_args__ = (UniqueConstraint("company_id", "doc_no", name="uq_ap_bills_company_no"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("companies.id"), nullable=False)
    doc_no: Mapped[str] = mapped_column(String(64), nullable=False)
    supplier_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("suppliers.id"), nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, default="CNY")
    exchange_rate: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False, default=1)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    base_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="open")
    bill_date: Mapped[date] = mapped_column(Date, nullable=False)


class ArBill(AuditMixin, Base):
    """Accounts receivable bill."""

    __tablename__ = "ar_bills"
    __table_args__ = (UniqueConstraint("company_id", "doc_no", name="uq_ar_bills_company_no"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("companies.id"), nullable=False)
    doc_no: Mapped[str] = mapped_column(String(64), nullable=False)
    customer_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("customers.id"), nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False, default="CNY")
    exchange_rate: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False, default=1)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    base_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    received_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="open")
    bill_date: Mapped[date] = mapped_column(Date, nullable=False)


class PaymentRecord(AuditMixin, Base):
    """AP payment record."""

    __tablename__ = "payment_records"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("companies.id"), nullable=False)
    ap_bill_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ap_bills.id"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    base_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False)
    exchange_rate: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False, default=1)
    pay_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="posted")
    remark: Mapped[str | None] = mapped_column(String(255), nullable=True)


class ReceiptRecord(AuditMixin, Base):
    """AR receipt record."""

    __tablename__ = "receipt_records"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("companies.id"), nullable=False)
    ar_bill_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("ar_bills.id"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    base_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False)
    exchange_rate: Mapped[Decimal] = mapped_column(Numeric(18, 8), nullable=False, default=1)
    pay_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="posted")
    remark: Mapped[str | None] = mapped_column(String(255), nullable=True)
