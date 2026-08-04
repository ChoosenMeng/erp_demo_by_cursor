"""M2 master-data ORM models."""

from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.shared.mixins import AuditMixin


class Currency(AuditMixin, Base):
    """Currency master (global, not company-scoped)."""

    __tablename__ = "currencies"

    code: Mapped[str] = mapped_column(String(3), primary_key=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    symbol: Mapped[str | None] = mapped_column(String(8), nullable=True)
    decimal_places: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")


class Customer(AuditMixin, Base):
    """Customer master, unique code per company."""

    __tablename__ = "customers"
    __table_args__ = (UniqueConstraint("company_id", "code", name="uq_customers_company_code"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("companies.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    contact_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    credit_limit: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")


class Supplier(AuditMixin, Base):
    """Supplier master, unique code per company."""

    __tablename__ = "suppliers"
    __table_args__ = (UniqueConstraint("company_id", "code", name="uq_suppliers_company_code"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("companies.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    contact_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")


class Material(AuditMixin, Base):
    """Material / product master."""

    __tablename__ = "materials"
    __table_args__ = (UniqueConstraint("company_id", "code", name="uq_materials_company_code"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("companies.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    spec: Mapped[str | None] = mapped_column(String(128), nullable=True)
    uom: Mapped[str] = mapped_column(String(16), nullable=False, default="pcs")
    material_type: Mapped[str] = mapped_column(String(32), nullable=False, default="finished")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")


class Warehouse(AuditMixin, Base):
    """Warehouse master."""

    __tablename__ = "warehouses"
    __table_args__ = (UniqueConstraint("company_id", "code", name="uq_warehouses_company_code"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("companies.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")
