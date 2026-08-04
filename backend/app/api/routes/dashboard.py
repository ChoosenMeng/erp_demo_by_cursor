"""Dashboard summary and trend APIs."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, require_permissions
from app.core.response import ok
from app.db.session import get_db
from app.modules.finance import services

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
def summary(
    ctx: Annotated[AuthContext, Depends(require_permissions("dashboard.read"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    return ok(services.dashboard_summary(db, ctx.company_id).model_dump(mode="json"))


@router.get("/sales-trend")
def sales_trend(
    ctx: Annotated[AuthContext, Depends(require_permissions("dashboard.read"))],
    db: Annotated[Session, Depends(get_db)],
    days: int = Query(7, ge=1, le=90),
) -> dict:
    return ok(services.sales_trend(db, ctx.company_id, days).model_dump(mode="json"))
