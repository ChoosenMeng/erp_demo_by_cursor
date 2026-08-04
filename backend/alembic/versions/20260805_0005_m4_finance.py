"""Create M4 AP/AR and payment tables.

Revision ID: 20260805_0005
Revises: 20260805_0004
Create Date: 2026-08-05
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.mysql import DATETIME

revision: str = "20260805_0005"
down_revision: Union[str, Sequence[str], None] = "20260805_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _audit_columns() -> list[sa.Column]:
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
    """Create finance tables."""
    op.create_table(
        "ap_bills",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("company_id", sa.BigInteger(), nullable=False),
        sa.Column("doc_no", sa.String(length=64), nullable=False),
        sa.Column("supplier_id", sa.BigInteger(), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("source_id", sa.BigInteger(), nullable=False),
        sa.Column("currency_code", sa.String(length=3), nullable=False),
        sa.Column("exchange_rate", sa.Numeric(18, 8), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("base_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("paid_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("bill_date", sa.Date(), nullable=False),
        *_audit_columns(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "doc_no", name="uq_ap_bills_company_no"),
    )

    op.create_table(
        "ar_bills",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("company_id", sa.BigInteger(), nullable=False),
        sa.Column("doc_no", sa.String(length=64), nullable=False),
        sa.Column("customer_id", sa.BigInteger(), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("source_id", sa.BigInteger(), nullable=False),
        sa.Column("currency_code", sa.String(length=3), nullable=False),
        sa.Column("exchange_rate", sa.Numeric(18, 8), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("base_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("received_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("bill_date", sa.Date(), nullable=False),
        *_audit_columns(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "doc_no", name="uq_ar_bills_company_no"),
    )

    op.create_table(
        "payment_records",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("company_id", sa.BigInteger(), nullable=False),
        sa.Column("ap_bill_id", sa.BigInteger(), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("base_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency_code", sa.String(length=3), nullable=False),
        sa.Column("exchange_rate", sa.Numeric(18, 8), nullable=False),
        sa.Column("pay_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("remark", sa.String(length=255), nullable=True),
        *_audit_columns(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["ap_bill_id"], ["ap_bills.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "receipt_records",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("company_id", sa.BigInteger(), nullable=False),
        sa.Column("ar_bill_id", sa.BigInteger(), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("base_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency_code", sa.String(length=3), nullable=False),
        sa.Column("exchange_rate", sa.Numeric(18, 8), nullable=False),
        sa.Column("pay_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("remark", sa.String(length=255), nullable=True),
        *_audit_columns(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["ar_bill_id"], ["ar_bills.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Drop finance tables."""
    op.drop_table("receipt_records")
    op.drop_table("payment_records")
    op.drop_table("ar_bills")
    op.drop_table("ap_bills")
