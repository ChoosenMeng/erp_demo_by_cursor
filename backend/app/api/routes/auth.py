"""Auth routes: login, refresh, logout, current user profile."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, get_auth_context, get_current_user
from app.core.response import ok
from app.db.session import get_db
from app.modules.org.models import User
from app.modules.org.schemas import LoginRequest, RefreshRequest, UserMe
from app.modules.org.services import build_user_me, login, refresh_tokens

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def auth_login(body: LoginRequest, db: Session = Depends(get_db)) -> dict:
    """Login with username/password; returns JWT pair + user profile."""
    result = login(db, body.username, body.password)
    return ok(result.model_dump())


@router.post("/refresh")
def auth_refresh(body: RefreshRequest, db: Session = Depends(get_db)) -> dict:
    """Exchange refresh token for a new access/refresh pair."""
    result = refresh_tokens(db, body.refresh_token)
    return ok(result.model_dump())


@router.post("/logout")
def auth_logout(_user: Annotated[User, Depends(get_current_user)]) -> dict:
    """Logout placeholder for stateless JWT (client should discard tokens)."""
    return ok({"logged_out": True}, message="请客户端丢弃本地 Token")


@router.get("/me")
def auth_me(
    ctx: Annotated[AuthContext, Depends(get_auth_context)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Return current user profile with active company from X-Company-Id / default."""
    profile: UserMe = build_user_me(db, ctx.user, active_company_id=ctx.company_id)
    return ok(profile.model_dump())
