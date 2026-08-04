"""Import all ORM models so Base.metadata is complete for Alembic."""

from app.modules.inventory.models import (  # noqa: F401
    InventoryBalance,
    InventoryTransaction,
)
from app.modules.master.models import (  # noqa: F401
    Currency,
    Customer,
    Material,
    Supplier,
    Warehouse,
)
from app.modules.org.models import (  # noqa: F401
    Company,
    Permission,
    Role,
    RolePermission,
    User,
    UserCompany,
    UserRole,
)
