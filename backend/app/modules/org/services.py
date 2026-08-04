"""Org / auth domain helpers."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.core.exceptions import UnauthorizedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
)
from app.modules.org.models import Permission, RolePermission, User, UserCompany, UserRole
from app.modules.org.schemas import CompanyBrief, TokenResponse, UserMe


def get_user_by_username(db: Session, username: str) -> User | None:
    """Load user by unique username."""
    return db.scalar(select(User).where(User.username == username))


def get_user_by_id(db: Session, user_id: int) -> User | None:
    """Load user by primary key."""
    return db.get(User, user_id)


def load_user_graph(db: Session, user_id: int) -> User | None:
    """Load user with roles and companies eagerly."""
    return db.scalar(
        select(User)
        .where(User.id == user_id)
        .options(
            selectinload(User.role_links).selectinload(UserRole.role),
            selectinload(User.company_links).selectinload(UserCompany.company),
        )
    )


def collect_role_codes(user: User) -> list[str]:
    """Return sorted unique role codes for a user."""
    return sorted({link.role.code for link in user.role_links if link.role})


def collect_permission_codes(db: Session, user: User) -> list[str]:
    """Return permission codes; admin role short-circuits to ['*']."""
    role_codes = collect_role_codes(user)
    if "admin" in role_codes:
        return ["*"]

    role_ids = [link.role_id for link in user.role_links]
    if not role_ids:
        return []

    rows = db.scalars(
        select(Permission.code)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .where(RolePermission.role_id.in_(role_ids))
        .distinct()
    ).all()
    return sorted(rows)


def build_user_me(db: Session, user: User) -> UserMe:
    """Build API user profile from ORM user."""
    companies = [
        CompanyBrief(
            id=link.company.id,
            code=link.company.code,
            name=link.company.name,
            is_default=link.is_default,
        )
        for link in user.company_links
        if link.company
    ]
    # Prefer default company; fall back to first linked company
    default_company_id = next((c.id for c in companies if c.is_default), None)
    if default_company_id is None and companies:
        default_company_id = companies[0].id

    return UserMe(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        roles=collect_role_codes(user),
        permissions=collect_permission_codes(db, user),
        companies=companies,
        company_id=default_company_id,
    )


def authenticate_user(db: Session, username: str, password: str) -> User:
    """Validate credentials; raise 401 on failure."""
    user = get_user_by_username(db, username)
    if user is None or not verify_password(password, user.password_hash):
        raise UnauthorizedError("用户名或密码错误")
    if user.status != "active":
        raise UnauthorizedError("用户已停用")
    return user


def login(db: Session, username: str, password: str) -> TokenResponse:
    """Authenticate and issue access + refresh tokens."""
    settings = get_settings()
    user = authenticate_user(db, username, password)

    # Reload with relationships for response payload
    user = load_user_graph(db, user.id)
    assert user is not None

    user.last_login_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.add(user)
    db.commit()

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        user=build_user_me(db, user),
    )
