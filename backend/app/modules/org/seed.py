"""Idempotent seed data for M1 (company, roles, permissions, admin)."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.modules.master.services import ensure_currency_cny
from app.modules.org.models import (
    Company,
    Permission,
    Role,
    RolePermission,
    User,
    UserCompany,
    UserRole,
)

# Demo credentials (development only)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# Org + master + inventory permissions (M1/M2)
PERMISSIONS: list[tuple[str, str, str]] = [
    ("org.company.read", "查看公司", "org"),
    ("org.company.write", "维护公司", "org"),
    ("org.user.read", "查看用户", "org"),
    ("org.user.write", "维护用户", "org"),
    ("org.role.read", "查看角色", "org"),
    ("org.role.write", "维护角色", "org"),
    ("master.read", "查看主数据", "master"),
    ("master.write", "维护主数据", "master"),
    ("inventory.read", "查看库存", "inventory"),
    ("inventory.adjust", "库存调整", "inventory"),
    ("purchase.read", "查看采购", "purchase"),
    ("purchase.write", "维护采购", "purchase"),
    ("sales.read", "查看销售", "sales"),
    ("sales.write", "维护销售", "sales"),
]

# role_code, role_name, description, permission_codes (empty = none; admin handled as *)
ROLES: list[tuple[str, str, str | None, list[str]]] = [
    ("admin", "系统管理员", "Full system access", []),
    (
        "sales",
        "业务员",
        "Sales operations",
        [
            "org.user.read",
            "master.read",
            "inventory.read",
            "sales.read",
            "sales.write",
        ],
    ),
    (
        "buyer",
        "采购员",
        "Purchase operations",
        [
            "org.user.read",
            "master.read",
            "inventory.read",
            "purchase.read",
            "purchase.write",
        ],
    ),
    (
        "warehouse",
        "仓管员",
        "Warehouse operations",
        [
            "org.user.read",
            "master.read",
            "inventory.read",
            "inventory.adjust",
            "purchase.read",
            "purchase.write",
            "sales.read",
            "sales.write",
        ],
    ),
    (
        "finance",
        "财务",
        "Finance operations",
        ["org.user.read", "master.read", "inventory.read"],
    ),
]


def _get_or_create_company(db: Session) -> Company:
    """Ensure default demo company exists."""
    company = db.scalar(select(Company).where(Company.code == "DEFAULT"))
    if company:
        return company
    company = Company(
        code="DEFAULT",
        name="演示公司",
        base_currency_code="CNY",
        status="active",
    )
    db.add(company)
    db.flush()
    return company


def _get_or_create_permission(db: Session, code: str, name: str, module: str) -> Permission:
    """Ensure a permission row exists."""
    row = db.scalar(select(Permission).where(Permission.code == code))
    if row:
        return row
    row = Permission(code=code, name=name, module=module)
    db.add(row)
    db.flush()
    return row


def _get_or_create_role(
    db: Session, code: str, name: str, description: str | None
) -> Role:
    """Ensure a role row exists."""
    row = db.scalar(select(Role).where(Role.code == code))
    if row:
        return row
    row = Role(code=code, name=name, description=description)
    db.add(row)
    db.flush()
    return row


def _ensure_role_permission(db: Session, role_id: int, permission_id: int) -> None:
    """Link role and permission if missing."""
    exists = db.scalar(
        select(RolePermission).where(
            RolePermission.role_id == role_id,
            RolePermission.permission_id == permission_id,
        )
    )
    if exists:
        return
    db.add(RolePermission(role_id=role_id, permission_id=permission_id))


def _get_or_create_admin(db: Session, company: Company, admin_role: Role) -> User:
    """Ensure admin user, role link, and default company link."""
    user = db.scalar(select(User).where(User.username == ADMIN_USERNAME))
    if user is None:
        user = User(
            username=ADMIN_USERNAME,
            password_hash=hash_password(ADMIN_PASSWORD),
            display_name="系统管理员",
            email="admin@example.com",
            status="active",
        )
        db.add(user)
        db.flush()

    # user <-> admin role
    has_role = db.scalar(
        select(UserRole).where(UserRole.user_id == user.id, UserRole.role_id == admin_role.id)
    )
    if not has_role:
        db.add(UserRole(user_id=user.id, role_id=admin_role.id))

    # user <-> default company
    has_company = db.scalar(
        select(UserCompany).where(
            UserCompany.user_id == user.id, UserCompany.company_id == company.id
        )
    )
    if not has_company:
        db.add(
            UserCompany(user_id=user.id, company_id=company.id, is_default=True)
        )

    return user


def run_seed(db: Session) -> dict:
    """Seed M1/M2 baseline data; safe to run multiple times."""
    company = _get_or_create_company(db)
    ensure_currency_cny(db)

    perm_map: dict[str, Permission] = {}
    for code, name, module in PERMISSIONS:
        perm_map[code] = _get_or_create_permission(db, code, name, module)

    role_map: dict[str, Role] = {}
    for code, name, description, perm_codes in ROLES:
        role = _get_or_create_role(db, code, name, description)
        role_map[code] = role
        for perm_code in perm_codes:
            _ensure_role_permission(db, role.id, perm_map[perm_code].id)

    # Admin role gets every permission row (API still exposes ['*'])
    admin_role = role_map["admin"]
    for perm in perm_map.values():
        _ensure_role_permission(db, admin_role.id, perm.id)

    admin = _get_or_create_admin(db, company, admin_role)
    db.commit()

    return {
        "company_id": company.id,
        "company_code": company.code,
        "admin_username": admin.username,
        "roles": sorted(role_map.keys()),
        "permissions": sorted(perm_map.keys()),
    }
