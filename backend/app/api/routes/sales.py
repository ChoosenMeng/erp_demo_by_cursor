"""Sales order and stock-out APIs."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, require_permissions
from app.core.response import ok
from app.db.session import get_db
from app.modules.trade import services
from app.modules.trade.schemas import SalesOrderCreate, SalesOrderUpdate, StockOutCreate

router = APIRouter(prefix="/sales", tags=["sales"])


@router.get("/orders")
def list_orders(
    ctx: Annotated[AuthContext, Depends(require_permissions("sales.read"))],
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> dict:
    data = services.list_sales_orders(db, ctx.company_id, page=page, page_size=page_size)
    return ok(
        {
            "items": [i.model_dump(mode="json") for i in data["items"]],
            "meta": data["meta"].model_dump(),
        }
    )


@router.post("/orders")
def create_order(
    body: SalesOrderCreate,
    ctx: Annotated[AuthContext, Depends(require_permissions("sales.write"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    return ok(
        services.create_sales_order(db, ctx.company_id, body, ctx.user.id).model_dump(
            mode="json"
        )
    )


@router.get("/orders/{so_id}")
def get_order(
    so_id: int,
    ctx: Annotated[AuthContext, Depends(require_permissions("sales.read"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    return ok(services.get_sales_order(db, ctx.company_id, so_id).model_dump(mode="json"))


@router.patch("/orders/{so_id}")
def update_order(
    so_id: int,
    body: SalesOrderUpdate,
    ctx: Annotated[AuthContext, Depends(require_permissions("sales.write"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    return ok(
        services.update_sales_order(
            db, ctx.company_id, so_id, body, ctx.user.id
        ).model_dump(mode="json")
    )


@router.post("/orders/{so_id}/confirm")
def confirm_order(
    so_id: int,
    ctx: Annotated[AuthContext, Depends(require_permissions("sales.write"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    return ok(
        services.confirm_sales_order(db, ctx.company_id, so_id, ctx.user.id).model_dump(
            mode="json"
        )
    )


@router.post("/orders/{so_id}/cancel")
def cancel_order(
    so_id: int,
    ctx: Annotated[AuthContext, Depends(require_permissions("sales.write"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    return ok(
        services.cancel_sales_order(db, ctx.company_id, so_id, ctx.user.id).model_dump(
            mode="json"
        )
    )


@router.get("/stock-outs")
def list_stock_outs(
    ctx: Annotated[AuthContext, Depends(require_permissions("sales.read"))],
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> dict:
    data = services.list_stock_outs(db, ctx.company_id, page=page, page_size=page_size)
    return ok(
        {
            "items": [i.model_dump(mode="json") for i in data["items"]],
            "meta": data["meta"].model_dump(),
        }
    )


@router.post("/stock-outs")
def create_stock_out(
    body: StockOutCreate,
    ctx: Annotated[AuthContext, Depends(require_permissions("sales.write"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    return ok(
        services.create_stock_out(db, ctx.company_id, body, ctx.user.id).model_dump(mode="json")
    )


@router.post("/stock-outs/{stock_out_id}/post")
def post_stock_out(
    stock_out_id: int,
    ctx: Annotated[AuthContext, Depends(require_permissions("sales.write"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    return ok(
        services.post_stock_out(db, ctx.company_id, stock_out_id, ctx.user.id).model_dump(
            mode="json"
        )
    )
