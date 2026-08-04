from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import get_settings
from app.core.response import ok
from app.db.session import engine

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict:
    settings = get_settings()
    db_status = "ok"
    db_name = None
    db_version = None

    try:
        with engine.connect() as conn:
            db_name = conn.execute(text("SELECT DATABASE()")).scalar()
            db_version = conn.execute(text("SELECT VERSION()")).scalar()
    except Exception as exc:  # noqa: BLE001 - surface connectivity in health payload
        db_status = f"error: {exc.__class__.__name__}"

    overall = "healthy" if db_status == "ok" else "degraded"

    return ok(
        {
            "status": overall,
            "app": settings.app_name,
            "env": settings.app_env,
            "database": {
                "status": db_status,
                "name": db_name,
                "version": db_version,
            },
        }
    )
