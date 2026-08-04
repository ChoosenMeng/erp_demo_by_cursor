"""Shared FastAPI dependencies (DB session, auth)."""

from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import UnauthorizedError
from app.core.security import safe_decode_token
from app.db.session import get_db
from app.modules.org.models import User
from app.modules.org.services import get_user_by_id

# Extract Bearer token from Authorization header
bearer_scheme = HTTPBearer(auto_error=False)

DbSession = Generator[Session, None, None]


def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
    ],
) -> User:
    """Resolve the current user from a valid access JWT."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise UnauthorizedError("缺少或无效的认证信息")

    payload = safe_decode_token(credentials.credentials)
    if payload is None:
        raise UnauthorizedError("Token 无效或已过期")
    if payload.get("type") != "access":
        raise UnauthorizedError("Token 类型错误")

    sub = payload.get("sub")
    if sub is None:
        raise UnauthorizedError("Token 无效或已过期")

    try:
        user_id = int(sub)
    except (TypeError, ValueError) as exc:
        raise UnauthorizedError("Token 无效或已过期") from exc

    user = get_user_by_id(db, user_id)
    if user is None or user.status != "active":
        raise UnauthorizedError("用户不存在或已停用")
    return user


__all__ = ["get_db", "get_current_user", "DbSession"]
