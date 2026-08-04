"""M1 organization / RBAC ORM models.

Tables: companies, users, roles, permissions,
        user_roles, role_permissions, user_companies.
"""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.mysql import DATETIME
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.shared.mixins import AuditMixin


class Company(AuditMixin, Base):
    """Tenant/company master. MVP usually has one active company."""

    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    # Company book currency (ISO 4217), default CNY
    base_currency_code: Mapped[str] = mapped_column(String(3), nullable=False, default="CNY")
    # active | inactive
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")

    user_links: Mapped[list["UserCompany"]] = relationship(back_populates="company")


class User(AuditMixin, Base):
    """Login account. Roles/companies are linked via junction tables."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(64), nullable=False)
    email: Mapped[str | None] = mapped_column(String(128), nullable=True)
    # active | disabled
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")
    last_login_at: Mapped[datetime | None] = mapped_column(DATETIME(fsp=6), nullable=True)

    role_links: Mapped[list["UserRole"]] = relationship(back_populates="user")
    company_links: Mapped[list["UserCompany"]] = relationship(back_populates="user")


class Role(AuditMixin, Base):
    """Named role that groups permissions (e.g. admin, buyer)."""

    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    user_links: Mapped[list["UserRole"]] = relationship(back_populates="role")
    permission_links: Mapped[list["RolePermission"]] = relationship(back_populates="role")


class Permission(AuditMixin, Base):
    """Fine-grained permission code used by API guards and menus."""

    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    # e.g. sales.order.create
    code: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    # Module group label, e.g. sales / org
    module: Mapped[str] = mapped_column(String(64), nullable=False)

    role_links: Mapped[list["RolePermission"]] = relationship(back_populates="permission")


class UserRole(AuditMixin, Base):
    """Many-to-many: user <-> role."""

    __tablename__ = "user_roles"
    __table_args__ = (UniqueConstraint("user_id", "role_id", name="uq_user_roles_user_role"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    role_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False
    )

    user: Mapped[User] = relationship(back_populates="role_links")
    role: Mapped[Role] = relationship(back_populates="user_links")


class RolePermission(AuditMixin, Base):
    """Many-to-many: role <-> permission."""

    __tablename__ = "role_permissions"
    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permissions_role_perm"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    role_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False
    )
    permission_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False
    )

    role: Mapped[Role] = relationship(back_populates="permission_links")
    permission: Mapped[Permission] = relationship(back_populates="role_links")


class UserCompany(AuditMixin, Base):
    """Many-to-many: user <-> company (multi-company ready)."""

    __tablename__ = "user_companies"
    __table_args__ = (
        UniqueConstraint("user_id", "company_id", name="uq_user_companies_user_company"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    company_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    # Prefer this company when X-Company-Id is omitted
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    user: Mapped[User] = relationship(back_populates="company_links")
    company: Mapped[Company] = relationship(back_populates="user_links")
