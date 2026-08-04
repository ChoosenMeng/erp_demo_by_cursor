"""Create M2 master data and inventory tables.

Revision ID: 20260805_0003
Revises: 20260805_0002
Create Date: 2026-08-05
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.mysql import DATETIME

revision: str = "20260805_0003"
down_revision: Union[str, Sequence[str], None] = "20260805_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _audit_columns() -> list[sa.Column]:
    """Shared audit columns required by docs/database.md §2.1."""
    return [
        sa.Column(
            "created_at",
            DATETIME(fsp=6),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP(6)"),
        ),
        sa.Column(
            "updated_at",
            DATETIME(fsp=6),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP(6)"),
        ),
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.Column("updated_by", sa.BigInteger(), nullable=True),
    ]


def upgrade() -> None:
    """Create currencies, master entities, and inventory tables."""
    op.create_table(
        "currencies",
        sa.Column("code", sa.String(length=3), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("symbol", sa.String(length=8), nullable=True),
        sa.Column("decimal_places", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        *_audit_columns(),
        sa.PrimaryKeyConstraint("code"),
    )

    op.create_table(
        "customers",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("company_id", sa.BigInteger(), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("contact_name", sa.String(length=64), nullable=True),
        sa.Column("contact_phone", sa.String(length=32), nullable=True),
        sa.Column("credit_limit", sa.Numeric(18, 2), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        *_audit_columns(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "code", name="uq_customers_company_code"),
    )

    op.create_table(
        "suppliers",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("company_id", sa.BigInteger(), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("contact_name", sa.String(length=64), nullable=True),
        sa.Column("contact_phone", sa.String(length=32), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        *_audit_columns(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "code", name="uq_suppliers_company_code"),
    )

    op.create_table(
        "materials",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("company_id", sa.BigInteger(), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("spec", sa.String(length=128), nullable=True),
        sa.Column("uom", sa.String(length=16), nullable=False),
        sa.Column("material_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        *_audit_columns(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "code", name="uq_materials_company_code"),
    )

    op.create_table(
        "warehouses",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("company_id", sa.BigInteger(), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        *_audit_columns(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "code", name="uq_warehouses_company_code"),
    )

    op.create_table(
        "inventory_balances",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("company_id", sa.BigInteger(), nullable=False),
        sa.Column("warehouse_id", sa.BigInteger(), nullable=False),
        sa.Column("material_id", sa.BigInteger(), nullable=False),
        sa.Column("qty_on_hand", sa.Numeric(18, 4), nullable=False),
        sa.Column("qty_available", sa.Numeric(18, 4), nullable=False),
        *_audit_columns(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["warehouse_id"], ["warehouses.id"]),
        sa.ForeignKeyConstraint(["material_id"], ["materials.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "warehouse_id", "material_id", name="uq_inventory_balances_cwm"),
    )

    op.create_table(
        "inventory_transactions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("company_id", sa.BigInteger(), nullable=False),
        sa.Column("warehouse_id", sa.BigInteger(), nullable=False),
        sa.Column("material_id", sa.BigInteger(), nullable=False),
        sa.Column("tx_type", sa.String(length=32), nullable=False),
        sa.Column("direction", sa.SmallInteger(), nullable=False),
        sa.Column("qty", sa.Numeric(18, 4), nullable=False),
        sa.Column("ref_doc_type", sa.String(length=32), nullable=True),
        sa.Column("ref_doc_id", sa.BigInteger(), nullable=True),
        sa.Column("ref_doc_no", sa.String(length=64), nullable=True),
        sa.Column("remark", sa.String(length=255), nullable=True),
        *_audit_columns(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["warehouse_id"], ["warehouses.id"]),
        sa.ForeignKeyConstraint(["material_id"], ["materials.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Drop M2 tables in reverse order."""
    op.drop_table("inventory_transactions")
    op.drop_table("inventory_balances")
    op.drop_table("warehouses")
    op.drop_table("materials")
    op.drop_table("suppliers")
    op.drop_table("customers")
    op.drop_table("currencies")
