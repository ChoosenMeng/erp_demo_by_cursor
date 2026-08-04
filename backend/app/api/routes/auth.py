"""Auth routes: login and current user profile."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.response import ok
from app.db.session import get_db
from app.modules.org.models import User
from app.modules.org.schemas import LoginRequest, UserMe
from app.modules.org.services import build_user_me, load_user_graph, login

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def auth_login(body: LoginRequest, db: Session = Depends(get_db)) -> dict:
    """Login with username/password; returns JWT pair + user profile."""
    result = login(db, body.username, body.password)
    return ok(result.model_dump())


@router.get("/me")
def auth_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Return current authenticated user profile."""
    # Reload graph so roles/companies are present
    user = load_user_graph(db, current_user.id)
    assert user is not None
    profile: UserMe = build_user_me(db, user)
    return ok(profile.model_dump())
