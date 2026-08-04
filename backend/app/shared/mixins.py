"""Reusable SQLAlchemy mixins shared across modules."""

from datetime import datetime

from sqlalchemy import BigInteger, func
from sqlalchemy.dialects.mysql import DATETIME
from sqlalchemy.orm import Mapped, mapped_column


class AuditMixin:
    """Adds mandatory audit columns to every business table.

    Fields: created_at, updated_at, created_by, updated_by.
    Spec: docs/database.md §2.1
    """

    # Row creation timestamp (DB default CURRENT_TIMESTAMP(6))
    created_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6),
        nullable=False,
        server_default=func.current_timestamp(6),
    )
    # Last update timestamp (refreshed on UPDATE)
    updated_at: Mapped[datetime] = mapped_column(
        DATETIME(fsp=6),
        nullable=False,
        server_default=func.current_timestamp(6),
        onupdate=func.current_timestamp(6),
    )
    # Creator user id (logical link to users.id; nullable for seed/system rows)
    created_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    # Last updater user id (logical link to users.id)
    updated_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
