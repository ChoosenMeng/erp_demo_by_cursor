"""M0 Alembic baseline (empty schema).

This is NOT a data backup. It only pins the migration chain start
so later revisions (e.g. M1 20260805_0002) can depend on it.
No business tables are created here.

Revision ID: 20260804_0001
Revises:
Create Date: 2026-08-04
"""

from typing import Sequence, Union

# Alembic revision identity
revision: str = "20260804_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Intentionally empty: business DDL starts from M1+.
    pass


def downgrade() -> None:
    # Nothing to drop for the empty baseline.
    pass
