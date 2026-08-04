"""Finance AP/AR APIs."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, require_permissions
from app.core.response import ok
from app.db.session import get_db
from app.modules.finance import services
from app.modules.finance.schemas import PaymentCreate, ReceiptCreate

router = APIRouter(prefix="/finance", tags=["finance"])


@router.get("/ap-bills")
def list_ap(
    ctx: Annotated[AuthContext, Depends(require_permissions("finance.read"))],
    db: Annotated[Session, Depends(get_db)],
    status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> dict:
    data = services.list_ap_bills(
        db, ctx.company_id, status=status, page=page, page_size=page_size
    )
    return ok(
        {
            "items": [i.model_dump(mode="json") for i in data["items"]],
            "meta": data["meta"].model_dump(),
        }
    )


@router.get("/ap-bills/{bill_id}")
def get_ap(
    bill_id: int,
    ctx: Annotated[AuthContext, Depends(require_permissions("finance.read"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    return ok(services.get_ap_bill(db, ctx.company_id, bill_id).model_dump(mode="json"))


@router.post("/ap-bills/{bill_id}/payments")
def pay_ap(
    bill_id: int,
    body: PaymentCreate,
    ctx: Annotated[AuthContext, Depends(require_permissions("finance.write"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    return ok(
        services.register_payment(
            db, ctx.company_id, bill_id, body, ctx.user.id
        ).model_dump(mode="json")
    )


@router.get("/ar-bills")
def list_ar(
    ctx: Annotated[AuthContext, Depends(require_permissions("finance.read"))],
    db: Annotated[Session, Depends(get_db)],
    status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> dict:
    data = services.list_ar_bills(
        db, ctx.company_id, status=status, page=page, page_size=page_size
    )
    return ok(
        {
            "items": [i.model_dump(mode="json") for i in data["items"]],
            "meta": data["meta"].model_dump(),
        }
    )


@router.get("/ar-bills/{bill_id}")
def get_ar(
    bill_id: int,
    ctx: Annotated[AuthContext, Depends(require_permissions("finance.read"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    return ok(services.get_ar_bill(db, ctx.company_id, bill_id).model_dump(mode="json"))


@router.post("/ar-bills/{bill_id}/receipts")
def receive_ar(
    bill_id: int,
    body: ReceiptCreate,
    ctx: Annotated[AuthContext, Depends(require_permissions("finance.write"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    return ok(
        services.register_receipt(
            db, ctx.company_id, bill_id, body, ctx.user.id
        ).model_dump(mode="json")
    )
