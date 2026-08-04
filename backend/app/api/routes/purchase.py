"""Purchase order and stock-in APIs."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, require_permissions
from app.core.response import ok
from app.db.session import get_db
from app.modules.trade import services
from app.modules.trade.schemas import PurchaseOrderCreate, PurchaseOrderUpdate, StockInCreate

router = APIRouter(prefix="/purchase", tags=["purchase"])


@router.get("/orders")
def list_orders(
    ctx: Annotated[AuthContext, Depends(require_permissions("purchase.read"))],
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> dict:
    data = services.list_purchase_orders(db, ctx.company_id, page=page, page_size=page_size)
    return ok(
        {
            "items": [i.model_dump(mode="json") for i in data["items"]],
            "meta": data["meta"].model_dump(),
        }
    )


@router.post("/orders")
def create_order(
    body: PurchaseOrderCreate,
    ctx: Annotated[AuthContext, Depends(require_permissions("purchase.write"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    return ok(
        services.create_purchase_order(db, ctx.company_id, body, ctx.user.id).model_dump(
            mode="json"
        )
    )


@router.get("/orders/{po_id}")
def get_order(
    po_id: int,
    ctx: Annotated[AuthContext, Depends(require_permissions("purchase.read"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    return ok(services.get_purchase_order(db, ctx.company_id, po_id).model_dump(mode="json"))


@router.patch("/orders/{po_id}")
def update_order(
    po_id: int,
    body: PurchaseOrderUpdate,
    ctx: Annotated[AuthContext, Depends(require_permissions("purchase.write"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    return ok(
        services.update_purchase_order(
            db, ctx.company_id, po_id, body, ctx.user.id
        ).model_dump(mode="json")
    )


@router.post("/orders/{po_id}/confirm")
def confirm_order(
    po_id: int,
    ctx: Annotated[AuthContext, Depends(require_permissions("purchase.write"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    return ok(
        services.confirm_purchase_order(db, ctx.company_id, po_id, ctx.user.id).model_dump(
            mode="json"
        )
    )


@router.post("/orders/{po_id}/cancel")
def cancel_order(
    po_id: int,
    ctx: Annotated[AuthContext, Depends(require_permissions("purchase.write"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    return ok(
        services.cancel_purchase_order(db, ctx.company_id, po_id, ctx.user.id).model_dump(
            mode="json"
        )
    )


@router.get("/stock-ins")
def list_stock_ins(
    ctx: Annotated[AuthContext, Depends(require_permissions("purchase.read"))],
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> dict:
    data = services.list_stock_ins(db, ctx.company_id, page=page, page_size=page_size)
    return ok(
        {
            "items": [i.model_dump(mode="json") for i in data["items"]],
            "meta": data["meta"].model_dump(),
        }
    )


@router.post("/stock-ins")
def create_stock_in(
    body: StockInCreate,
    ctx: Annotated[AuthContext, Depends(require_permissions("purchase.write"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    return ok(
        services.create_stock_in(db, ctx.company_id, body, ctx.user.id).model_dump(mode="json")
    )


@router.post("/stock-ins/{stock_in_id}/post")
def post_stock_in(
    stock_in_id: int,
    ctx: Annotated[AuthContext, Depends(require_permissions("purchase.write"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    return ok(
        services.post_stock_in(db, ctx.company_id, stock_in_id, ctx.user.id).model_dump(
            mode="json"
        )
    )
