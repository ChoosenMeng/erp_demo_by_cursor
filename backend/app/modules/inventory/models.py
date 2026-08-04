"""M2 inventory ORM models."""

from decimal import Decimal

from sqlalchemy import BigInteger, ForeignKey, Numeric, SmallInteger, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.shared.mixins import AuditMixin


class InventoryBalance(AuditMixin, Base):
    """On-hand / available qty per company + warehouse + material."""

    __tablename__ = "inventory_balances"
    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "warehouse_id",
            "material_id",
            name="uq_inventory_balances_cwm",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("companies.id"), nullable=False)
    warehouse_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("warehouses.id"), nullable=False
    )
    material_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("materials.id"), nullable=False)
    qty_on_hand: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0)
    qty_available: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=0)


class InventoryTransaction(AuditMixin, Base):
    """Immutable-ish stock movement ledger row."""

    __tablename__ = "inventory_transactions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("companies.id"), nullable=False)
    warehouse_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("warehouses.id"), nullable=False
    )
    material_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("materials.id"), nullable=False)
    tx_type: Mapped[str] = mapped_column(String(32), nullable=False)  # in / out / adjust
    direction: Mapped[int] = mapped_column(SmallInteger, nullable=False)  # 1 or -1
    qty: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    ref_doc_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    ref_doc_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    ref_doc_no: Mapped[str | None] = mapped_column(String(64), nullable=True)
    remark: Mapped[str | None] = mapped_column(String(255), nullable=True)
