"""Shared FastAPI dependencies (DB session, auth, company, permissions)."""

from collections.abc import Callable, Generator
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import safe_decode_token
from app.db.session import get_db
from app.modules.org.models import User, UserCompany
from app.modules.org.services import (
    collect_permission_codes,
    get_user_by_id,
    load_user_graph,
)

# Extract Bearer token from Authorization header
bearer_scheme = HTTPBearer(auto_error=False)

DbSession = Generator[Session, None, None]


@dataclass
class AuthContext:
    """Authenticated user + active company + permission codes."""

    user: User
    company_id: int
    permissions: list[str]


def _parse_user_id_from_access_token(token: str) -> int:
    """Validate access JWT and return user id."""
    payload = safe_decode_token(token)
    if payload is None:
        raise UnauthorizedError("Token 无效或已过期")
    if payload.get("type") != "access":
        raise UnauthorizedError("Token 类型错误")
    sub = payload.get("sub")
    try:
        return int(sub)
    except (TypeError, ValueError) as exc:
        raise UnauthorizedError("Token 无效或已过期") from exc


def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
    ],
) -> User:
    """Resolve the current user from a valid access JWT."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedError("缺少或无效的认证信息")

    user_id = _parse_user_id_from_access_token(credentials.credentials)
    user = get_user_by_id(db, user_id)
    if user is None or user.status != "active":
        raise UnauthorizedError("用户不存在或已停用")
    return user


def get_auth_context(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    x_company_id: Annotated[str | None, Header(alias="X-Company-Id")] = None,
) -> AuthContext:
    """Build auth context with company scope from header or default company."""
    user = load_user_graph(db, current_user.id)
    assert user is not None

    # Active company membership only (ignore inactive / retired companies)
    active_links = [
        link
        for link in user.company_links
        if link.company is not None and link.company.status == "active"
    ]
    company_ids = {link.company_id for link in active_links}
    if not company_ids:
        raise ForbiddenError("用户未关联任何公司")

    parsed_company_id: int | None = None
    if x_company_id is not None and str(x_company_id).strip() != "":
        try:
            parsed_company_id = int(str(x_company_id).strip())
        except ValueError as exc:
            raise ForbiddenError("无效的公司上下文") from exc

    if parsed_company_id is None:
        default_id = next(
            (link.company_id for link in active_links if link.is_default),
            None,
        )
        company_id = default_id if default_id is not None else next(iter(company_ids))
    else:
        if parsed_company_id not in company_ids:
            raise ForbiddenError("无权访问该公司")
        company_id = parsed_company_id

    permissions = collect_permission_codes(db, user)
    return AuthContext(user=user, company_id=company_id, permissions=permissions)


def user_has_permission(permissions: list[str], required: str) -> bool:
    """Return True if user has wildcard or the exact permission code."""
    return "*" in permissions or required in permissions


def require_permissions(*required: str) -> Callable[..., AuthContext]:
    """Dependency factory: require login + any listed permission codes."""

    def _checker(
        ctx: Annotated[AuthContext, Depends(get_auth_context)],
    ) -> AuthContext:
        if not required:
            return ctx
        if "*" in ctx.permissions:
            return ctx
        if any(code in ctx.permissions for code in required):
            return ctx
        raise ForbiddenError("无权限")

    return _checker


def ensure_user_in_company(db: Session, user_id: int, company_id: int) -> None:
    """Raise 403 if user is not linked to company."""
    exists = db.scalar(
        select(UserCompany.id).where(
            UserCompany.user_id == user_id,
            UserCompany.company_id == company_id,
        )
    )
    if exists is None:
        raise ForbiddenError("无权访问该公司")


__all__ = [
    "get_db",
    "get_current_user",
    "get_auth_context",
    "require_permissions",
    "AuthContext",
    "DbSession",
    "user_has_permission",
    "ensure_user_in_company",
]
