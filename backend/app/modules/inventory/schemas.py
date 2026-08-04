"""Pydantic schemas for inventory APIs."""

from decimal import Decimal

from pydantic import BaseModel, Field

from app.modules.org.schemas import PageMeta


class InventoryBalanceOut(BaseModel):
    """Balance row with display names."""

    id: int
    company_id: int
    warehouse_id: int
    warehouse_name: str
    material_id: int
    material_code: str
    material_name: str
    qty_on_hand: Decimal
    qty_available: Decimal


class InventoryTransactionOut(BaseModel):
    """Stock movement ledger row."""

    id: int
    company_id: int
    warehouse_id: int
    material_id: int
    tx_type: str
    direction: int
    qty: Decimal
    ref_doc_type: str | None
    ref_doc_id: int | None
    ref_doc_no: str | None
    remark: str | None


class InventoryAdjustRequest(BaseModel):
    """Debug adjust: direction 1=in, -1=out."""

    warehouse_id: int
    material_id: int
    direction: int = Field(description="1 inbound, -1 outbound")
    qty: Decimal = Field(gt=0)
    remark: str | None = Field(default=None, max_length=255)


__all__ = [
    "PageMeta",
    "InventoryBalanceOut",
    "InventoryTransactionOut",
    "InventoryAdjustRequest",
]
