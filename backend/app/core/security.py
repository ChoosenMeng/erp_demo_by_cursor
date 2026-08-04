"""Password hashing and JWT helpers."""

from datetime import datetime, timedelta, timezone
from typing import Any, Literal

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

# bcrypt via passlib
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

TokenType = Literal["access", "refresh"]


def hash_password(plain: str) -> str:
    """Hash a plain-text password."""
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify plain-text password against stored hash."""
    return pwd_context.verify(plain, hashed)


def create_token(
    *,
    subject: str,
    token_type: TokenType,
    expires_delta: timedelta,
    extra: dict[str, Any] | None = None,
) -> str:
    """Create a signed JWT (access or refresh)."""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def create_access_token(user_id: int) -> str:
    """Short-lived access token for API calls."""
    settings = get_settings()
    return create_token(
        subject=str(user_id),
        token_type="access",
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )


def create_refresh_token(user_id: int) -> str:
    """Longer-lived refresh token (stored client-side for now)."""
    settings = get_settings()
    return create_token(
        subject=str(user_id),
        token_type="refresh",
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
    )


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate JWT; raise JWTError if invalid/expired."""
    settings = get_settings()
    return jwt.decode(token, settings.secret_key, algorithms=["HS256"])


def safe_decode_token(token: str) -> dict[str, Any] | None:
    """Decode JWT or return None on failure."""
    try:
        return decode_token(token)
    except JWTError:
        return None
