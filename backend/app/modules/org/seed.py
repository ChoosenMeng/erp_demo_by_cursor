"""Idempotent seed data for org, roles, permissions, multi-company users."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.modules.master.services import ensure_currencies
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
DEMO_PASSWORD = "demo123"

# Active demo entities (DEFAULT kept but inactive)
ACTIVE_COMPANY_CODES = ("USCO", "EUCO")

# Companies: code, name, base_currency, initial_status
COMPANIES: list[tuple[str, str, str, str]] = [
    ("DEFAULT", "演示公司（中国）", "CNY", "inactive"),
    ("USCO", "US Demo Corp", "USD", "active"),
    ("EUCO", "EU Demo GmbH", "EUR", "active"),
]

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
    ("finance.read", "查看财务", "finance"),
    ("finance.write", "维护财务", "finance"),
    ("dashboard.read", "查看仪表盘", "dashboard"),
]

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
            "dashboard.read",
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
            "dashboard.read",
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
        [
            "org.user.read",
            "master.read",
            "inventory.read",
            "finance.read",
            "finance.write",
            "dashboard.read",
        ],
    ),
]

# username, display_name, email, role_codes, company_codes, default_company_code
DEMO_USERS: list[tuple[str, str, str, list[str], list[str], str]] = [
    (
        "sales_us",
        "US Sales",
        "sales_us@example.com",
        ["sales"],
        ["USCO"],
        "USCO",
    ),
    (
        "buyer_us",
        "US Buyer",
        "buyer_us@example.com",
        ["buyer"],
        ["USCO"],
        "USCO",
    ),
    (
        "sales_eu",
        "EU Sales",
        "sales_eu@example.com",
        ["sales"],
        ["EUCO"],
        "EUCO",
    ),
    (
        "wh_eu",
        "EU Warehouse",
        "wh_eu@example.com",
        ["warehouse"],
        ["EUCO"],
        "EUCO",
    ),
    (
        "finance_all",
        "Group Finance",
        "finance@example.com",
        ["finance"],
        ["USCO", "EUCO"],
        "USCO",
    ),
]


def _get_or_create_company(
    db: Session, code: str, name: str, base_currency: str, status: str
) -> Company:
    """Ensure a company exists with intended currency/status."""
    company = db.scalar(select(Company).where(Company.code == code))
    if company:
        company.name = name
        company.base_currency_code = base_currency
        company.status = status
        return company
    company = Company(
        code=code,
        name=name,
        base_currency_code=base_currency,
        status=status,
    )
    db.add(company)
    db.flush()
    return company


def _get_or_create_permission(db: Session, code: str, name: str, module: str) -> Permission:
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
    row = db.scalar(select(Role).where(Role.code == code))
    if row:
        return row
    row = Role(code=code, name=name, description=description)
    db.add(row)
    db.flush()
    return row


def _ensure_role_permission(db: Session, role_id: int, permission_id: int) -> None:
    exists = db.scalar(
        select(RolePermission).where(
            RolePermission.role_id == role_id,
            RolePermission.permission_id == permission_id,
        )
    )
    if exists:
        return
    db.add(RolePermission(role_id=role_id, permission_id=permission_id))


def _ensure_user_role(db: Session, user_id: int, role_id: int) -> None:
    exists = db.scalar(
        select(UserRole).where(UserRole.user_id == user_id, UserRole.role_id == role_id)
    )
    if exists:
        return
    db.add(UserRole(user_id=user_id, role_id=role_id))


def _ensure_user_company(
    db: Session, user_id: int, company_id: int, *, is_default: bool
) -> None:
    link = db.scalar(
        select(UserCompany).where(
            UserCompany.user_id == user_id, UserCompany.company_id == company_id
        )
    )
    if link is None:
        db.add(
            UserCompany(
                user_id=user_id,
                company_id=company_id,
                is_default=is_default,
            )
        )
        return
    if is_default and not link.is_default:
        for other in db.scalars(
            select(UserCompany).where(
                UserCompany.user_id == user_id, UserCompany.is_default.is_(True)
            )
        ).all():
            other.is_default = False
        link.is_default = True


def _unlink_user_company(db: Session, user_id: int, company_id: int) -> None:
    link = db.scalar(
        select(UserCompany).where(
            UserCompany.user_id == user_id, UserCompany.company_id == company_id
        )
    )
    if link:
        db.delete(link)


def _get_or_create_user(
    db: Session,
    username: str,
    password: str,
    display_name: str,
    email: str,
) -> User:
    user = db.scalar(select(User).where(User.username == username))
    if user:
        return user
    user = User(
        username=username,
        password_hash=hash_password(password),
        display_name=display_name,
        email=email,
        status="active",
    )
    db.add(user)
    db.flush()
    return user


def _drop_inactive_memberships(db: Session, companies: dict[str, Company]) -> None:
    """Remove user links to inactive companies (DEFAULT / SECOND)."""
    inactive_ids = [c.id for c in companies.values() if c.status != "active"]
    legacy = db.scalar(select(Company).where(Company.code == "SECOND"))
    if legacy:
        legacy.status = "inactive"
        inactive_ids.append(legacy.id)
    if not inactive_ids:
        return
    for link in db.scalars(
        select(UserCompany).where(UserCompany.company_id.in_(inactive_ids))
    ).all():
        db.delete(link)


def _seed_admin(
    db: Session, companies: dict[str, Company], admin_role: Role
) -> User:
    """Admin linked only to active entities; default USCO."""
    user = _get_or_create_user(
        db,
        ADMIN_USERNAME,
        ADMIN_PASSWORD,
        "系统管理员",
        "admin@example.com",
    )
    _ensure_user_role(db, user.id, admin_role.id)
    for code in ACTIVE_COMPANY_CODES:
        _ensure_user_company(
            db, user.id, companies[code].id, is_default=(code == "USCO")
        )
    if "DEFAULT" in companies:
        _unlink_user_company(db, user.id, companies["DEFAULT"].id)
    return user


def _seed_demo_users(
    db: Session, companies: dict[str, Company], role_map: dict[str, Role]
) -> list[str]:
    created: list[str] = []
    for username, display_name, email, role_codes, company_codes, default_code in DEMO_USERS:
        user = _get_or_create_user(db, username, DEMO_PASSWORD, display_name, email)
        for role_code in role_codes:
            _ensure_user_role(db, user.id, role_map[role_code].id)
        for company_code in company_codes:
            _ensure_user_company(
                db,
                user.id,
                companies[company_code].id,
                is_default=(company_code == default_code),
            )
        created.append(username)
    return created


def run_seed(db: Session) -> dict:
    """Seed permissions/roles/companies/users; safe to run multiple times."""
    ensure_currencies(db)

    companies = {
        code: _get_or_create_company(db, code, name, currency, status)
        for code, name, currency, status in COMPANIES
    }
    _drop_inactive_memberships(db, companies)

    perm_map: dict[str, Permission] = {}
    for code, name, module in PERMISSIONS:
        perm_map[code] = _get_or_create_permission(db, code, name, module)

    role_map: dict[str, Role] = {}
    for code, name, description, perm_codes in ROLES:
        role = _get_or_create_role(db, code, name, description)
        role_map[code] = role
        for perm_code in perm_codes:
            _ensure_role_permission(db, role.id, perm_map[perm_code].id)

    admin_role = role_map["admin"]
    for perm in perm_map.values():
        _ensure_role_permission(db, admin_role.id, perm.id)

    admin = _seed_admin(db, companies, admin_role)
    demo_users = _seed_demo_users(db, companies, role_map)
    db.commit()

    return {
        "company_id": companies["USCO"].id,
        "company_code": "USCO",
        "companies": sorted(ACTIVE_COMPANY_CODES),
        "inactive_companies": ["DEFAULT"],
        "admin_username": admin.username,
        "demo_users": demo_users,
        "demo_password": DEMO_PASSWORD,
        "roles": sorted(role_map.keys()),
        "permissions": sorted(perm_map.keys()),
    }
