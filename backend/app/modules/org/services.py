"""Org / auth domain helpers and CRUD services."""

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.core.exceptions import AppError, NotFoundError, UnauthorizedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    safe_decode_token,
    verify_password,
)
from app.modules.org.models import (
    Company,
    Permission,
    Role,
    RolePermission,
    User,
    UserCompany,
    UserRole,
)
from app.modules.org.schemas import (
    CompanyCreate,
    CompanyOut,
    CompanyUpdate,
    PageMeta,
    PermissionOut,
    RoleCreate,
    RoleOut,
    TokenResponse,
    UserCreate,
    UserMe,
    UserOut,
    UserUpdate,
    CompanyBrief,
)


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


def build_user_me(
    db: Session, user: User, *, active_company_id: int | None = None
) -> UserMe:
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
    default_company_id = next((c.id for c in companies if c.is_default), None)
    if default_company_id is None and companies:
        default_company_id = companies[0].id

    company_id = active_company_id if active_company_id is not None else default_company_id

    return UserMe(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        roles=collect_role_codes(user),
        permissions=collect_permission_codes(db, user),
        companies=companies,
        company_id=company_id,
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


def refresh_tokens(db: Session, refresh_token: str) -> TokenResponse:
    """Issue a new token pair from a valid refresh token."""
    settings = get_settings()
    payload = safe_decode_token(refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise UnauthorizedError("Refresh Token 无效或已过期")
    try:
        user_id = int(payload.get("sub"))
    except (TypeError, ValueError) as exc:
        raise UnauthorizedError("Refresh Token 无效或已过期") from exc

    user = load_user_graph(db, user_id)
    if user is None or user.status != "active":
        raise UnauthorizedError("用户不存在或已停用")

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        user=build_user_me(db, user),
    )


def _user_out(user: User) -> UserOut:
    """Map ORM user to list/detail DTO."""
    return UserOut(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        email=user.email,
        status=user.status,
        roles=collect_role_codes(user),
    )


def list_companies(db: Session, *, page: int, page_size: int) -> dict:
    """Paginate companies."""
    total = db.scalar(select(func.count()).select_from(Company)) or 0
    rows = db.scalars(
        select(Company).order_by(Company.id).offset((page - 1) * page_size).limit(page_size)
    ).all()
    items = [
        CompanyOut(
            id=r.id,
            code=r.code,
            name=r.name,
            base_currency_code=r.base_currency_code,
            status=r.status,
        )
        for r in rows
    ]
    return {"items": items, "meta": PageMeta(page=page, page_size=page_size, total=total)}


def create_company(db: Session, body: CompanyCreate, actor_id: int) -> CompanyOut:
    """Create a company row."""
    exists = db.scalar(select(Company.id).where(Company.code == body.code))
    if exists:
        raise AppError("公司编码已存在", code=40001, status_code=400)
    row = Company(
        code=body.code,
        name=body.name,
        base_currency_code=body.base_currency_code.upper(),
        status=body.status,
        created_by=actor_id,
        updated_by=actor_id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return CompanyOut(
        id=row.id,
        code=row.code,
        name=row.name,
        base_currency_code=row.base_currency_code,
        status=row.status,
    )


def get_company(db: Session, company_id: int) -> CompanyOut:
    """Get company by id."""
    row = db.get(Company, company_id)
    if row is None:
        raise NotFoundError("公司不存在")
    return CompanyOut(
        id=row.id,
        code=row.code,
        name=row.name,
        base_currency_code=row.base_currency_code,
        status=row.status,
    )


def update_company(
    db: Session, company_id: int, body: CompanyUpdate, actor_id: int
) -> CompanyOut:
    """Patch company fields."""
    row = db.get(Company, company_id)
    if row is None:
        raise NotFoundError("公司不存在")
    if body.name is not None:
        row.name = body.name
    if body.base_currency_code is not None:
        row.base_currency_code = body.base_currency_code.upper()
    if body.status is not None:
        row.status = body.status
    row.updated_by = actor_id
    db.add(row)
    db.commit()
    db.refresh(row)
    return CompanyOut(
        id=row.id,
        code=row.code,
        name=row.name,
        base_currency_code=row.base_currency_code,
        status=row.status,
    )


def list_users(db: Session, *, page: int, page_size: int) -> dict:
    """Paginate users with roles."""
    total = db.scalar(select(func.count()).select_from(User)) or 0
    rows = db.scalars(
        select(User)
        .options(selectinload(User.role_links).selectinload(UserRole.role))
        .order_by(User.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return {
        "items": [_user_out(u) for u in rows],
        "meta": PageMeta(page=page, page_size=page_size, total=total),
    }


def create_user(db: Session, body: UserCreate, actor_id: int) -> UserOut:
    """Create user and optional role/company links."""
    if get_user_by_username(db, body.username):
        raise AppError("用户名已存在", code=40001, status_code=400)

    user = User(
        username=body.username,
        password_hash=hash_password(body.password),
        display_name=body.display_name,
        email=body.email,
        status=body.status,
        created_by=actor_id,
        updated_by=actor_id,
    )
    db.add(user)
    db.flush()

    for role_id in body.role_ids:
        if db.get(Role, role_id) is None:
            raise NotFoundError(f"角色不存在: {role_id}")
        db.add(UserRole(user_id=user.id, role_id=role_id, created_by=actor_id, updated_by=actor_id))

    company_ids = body.company_ids or []
    default_id = body.default_company_id
    if default_id is not None and default_id not in company_ids:
        company_ids.append(default_id)
    for company_id in company_ids:
        if db.get(Company, company_id) is None:
            raise NotFoundError(f"公司不存在: {company_id}")
        db.add(
            UserCompany(
                user_id=user.id,
                company_id=company_id,
                is_default=(company_id == default_id) if default_id else False,
                created_by=actor_id,
                updated_by=actor_id,
            )
        )

    db.commit()
    loaded = load_user_graph(db, user.id)
    assert loaded is not None
    return _user_out(loaded)


def get_user(db: Session, user_id: int) -> UserOut:
    """Get user detail."""
    user = load_user_graph(db, user_id)
    if user is None:
        raise NotFoundError("用户不存在")
    return _user_out(user)


def update_user(db: Session, user_id: int, body: UserUpdate, actor_id: int) -> UserOut:
    """Patch user profile / status / password."""
    user = db.get(User, user_id)
    if user is None:
        raise NotFoundError("用户不存在")
    if body.display_name is not None:
        user.display_name = body.display_name
    if body.email is not None:
        user.email = body.email
    if body.status is not None:
        user.status = body.status
    if body.password is not None:
        user.password_hash = hash_password(body.password)
    user.updated_by = actor_id
    db.add(user)
    db.commit()
    loaded = load_user_graph(db, user_id)
    assert loaded is not None
    return _user_out(loaded)


def set_user_roles(db: Session, user_id: int, role_ids: list[int], actor_id: int) -> UserOut:
    """Replace all roles for a user."""
    user = db.get(User, user_id)
    if user is None:
        raise NotFoundError("用户不存在")

    existing = db.scalars(select(UserRole).where(UserRole.user_id == user_id)).all()
    for link in existing:
        db.delete(link)
    db.flush()

    for role_id in role_ids:
        if db.get(Role, role_id) is None:
            raise NotFoundError(f"角色不存在: {role_id}")
        db.add(UserRole(user_id=user_id, role_id=role_id, created_by=actor_id, updated_by=actor_id))

    db.commit()
    loaded = load_user_graph(db, user_id)
    assert loaded is not None
    return _user_out(loaded)


def _role_out(db: Session, role: Role) -> RoleOut:
    """Map role + permission codes."""
    codes = db.scalars(
        select(Permission.code)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .where(RolePermission.role_id == role.id)
        .order_by(Permission.code)
    ).all()
    return RoleOut(
        id=role.id,
        code=role.code,
        name=role.name,
        description=role.description,
        permission_codes=list(codes),
    )


def list_roles(db: Session) -> list[RoleOut]:
    """List all roles."""
    rows = db.scalars(select(Role).order_by(Role.id)).all()
    return [_role_out(db, r) for r in rows]


def create_role(db: Session, body: RoleCreate, actor_id: int) -> RoleOut:
    """Create a role."""
    exists = db.scalar(select(Role.id).where(Role.code == body.code))
    if exists:
        raise AppError("角色编码已存在", code=40001, status_code=400)
    role = Role(
        code=body.code,
        name=body.name,
        description=body.description,
        created_by=actor_id,
        updated_by=actor_id,
    )
    db.add(role)
    db.commit()
    db.refresh(role)
    return _role_out(db, role)


def set_role_permissions(
    db: Session, role_id: int, permission_ids: list[int], actor_id: int
) -> RoleOut:
    """Replace permissions bound to a role."""
    role = db.get(Role, role_id)
    if role is None:
        raise NotFoundError("角色不存在")

    existing = db.scalars(select(RolePermission).where(RolePermission.role_id == role_id)).all()
    for link in existing:
        db.delete(link)
    db.flush()

    for permission_id in permission_ids:
        if db.get(Permission, permission_id) is None:
            raise NotFoundError(f"权限不存在: {permission_id}")
        db.add(
            RolePermission(
                role_id=role_id,
                permission_id=permission_id,
                created_by=actor_id,
                updated_by=actor_id,
            )
        )

    db.commit()
    return _role_out(db, role)


def list_permissions(db: Session) -> list[PermissionOut]:
    """List all permission codes."""
    rows = db.scalars(select(Permission).order_by(Permission.module, Permission.code)).all()
    return [
        PermissionOut(id=r.id, code=r.code, name=r.name, module=r.module) for r in rows
    ]
