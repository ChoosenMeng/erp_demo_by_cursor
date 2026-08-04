"""Inventory query and debug adjust APIs."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, require_permissions
from app.core.response import ok
from app.db.session import get_db
from app.modules.inventory import services
from app.modules.inventory.schemas import InventoryAdjustRequest

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("/balances")
def list_balances(
    ctx: Annotated[AuthContext, Depends(require_permissions("inventory.read"))],
    db: Annotated[Session, Depends(get_db)],
    warehouse_id: int | None = None,
    material_id: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> dict:
    """List inventory balances for active company."""
    data = services.list_balances(
        db,
        ctx.company_id,
        warehouse_id=warehouse_id,
        material_id=material_id,
        page=page,
        page_size=page_size,
    )
    return ok(
        {
            "items": [i.model_dump(mode="json") for i in data["items"]],
            "meta": data["meta"].model_dump(),
        }
    )


@router.get("/transactions")
def list_transactions(
    ctx: Annotated[AuthContext, Depends(require_permissions("inventory.read"))],
    db: Annotated[Session, Depends(get_db)],
    warehouse_id: int | None = None,
    material_id: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> dict:
    """List inventory transactions."""
    data = services.list_transactions(
        db,
        ctx.company_id,
        warehouse_id=warehouse_id,
        material_id=material_id,
        page=page,
        page_size=page_size,
    )
    return ok(
        {
            "items": [i.model_dump(mode="json") for i in data["items"]],
            "meta": data["meta"].model_dump(),
        }
    )


@router.post("/adjust")
def adjust_stock(
    body: InventoryAdjustRequest,
    ctx: Annotated[AuthContext, Depends(require_permissions("inventory.adjust"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Debug stock adjust (in/out)."""
    return ok(
        services.adjust_stock(db, ctx.company_id, body, ctx.user.id).model_dump(
            mode="json"
        )
    )
