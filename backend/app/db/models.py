"""Import all ORM models so Base.metadata is complete for Alembic."""

from app.modules.org.models import (  # noqa: F401
    Company,
    Permission,
    Role,
    RolePermission,
    User,
    UserCompany,
    UserRole,
)
