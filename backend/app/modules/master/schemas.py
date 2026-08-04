"""Pydantic schemas for master-data APIs."""

from decimal import Decimal

from pydantic import BaseModel, Field

from app.modules.org.schemas import PageMeta


class CurrencyCreate(BaseModel):
    """Create currency payload."""

    code: str = Field(min_length=3, max_length=3)
    name: str = Field(min_length=1, max_length=64)
    symbol: str | None = Field(default=None, max_length=8)
    decimal_places: int = Field(default=2, ge=0, le=8)
    status: str = Field(default="active", max_length=16)


class CurrencyOut(BaseModel):
    """Currency response row."""

    code: str
    name: str
    symbol: str | None
    decimal_places: int
    status: str


class CustomerCreate(BaseModel):
    """Create customer payload."""

    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=128)
    contact_name: str | None = Field(default=None, max_length=64)
    contact_phone: str | None = Field(default=None, max_length=32)
    credit_limit: Decimal | None = None
    status: str = Field(default="active", max_length=16)


class CustomerUpdate(BaseModel):
    """Patch customer payload."""

    name: str | None = Field(default=None, max_length=128)
    contact_name: str | None = Field(default=None, max_length=64)
    contact_phone: str | None = Field(default=None, max_length=32)
    credit_limit: Decimal | None = None
    status: str | None = Field(default=None, max_length=16)


class CustomerOut(BaseModel):
    """Customer response row."""

    id: int
    company_id: int
    code: str
    name: str
    contact_name: str | None
    contact_phone: str | None
    credit_limit: Decimal | None
    status: str


class SupplierCreate(BaseModel):
    """Create supplier payload."""

    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=128)
    contact_name: str | None = Field(default=None, max_length=64)
    contact_phone: str | None = Field(default=None, max_length=32)
    status: str = Field(default="active", max_length=16)


class SupplierUpdate(BaseModel):
    """Patch supplier payload."""

    name: str | None = Field(default=None, max_length=128)
    contact_name: str | None = Field(default=None, max_length=64)
    contact_phone: str | None = Field(default=None, max_length=32)
    status: str | None = Field(default=None, max_length=16)


class SupplierOut(BaseModel):
    """Supplier response row."""

    id: int
    company_id: int
    code: str
    name: str
    contact_name: str | None
    contact_phone: str | None
    status: str


class MaterialCreate(BaseModel):
    """Create material payload."""

    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=128)
    spec: str | None = Field(default=None, max_length=128)
    uom: str = Field(default="pcs", min_length=1, max_length=16)
    material_type: str = Field(default="finished", max_length=32)
    status: str = Field(default="active", max_length=16)


class MaterialUpdate(BaseModel):
    """Patch material payload."""

    name: str | None = Field(default=None, max_length=128)
    spec: str | None = Field(default=None, max_length=128)
    uom: str | None = Field(default=None, max_length=16)
    material_type: str | None = Field(default=None, max_length=32)
    status: str | None = Field(default=None, max_length=16)


class MaterialOut(BaseModel):
    """Material response row."""

    id: int
    company_id: int
    code: str
    name: str
    spec: str | None
    uom: str
    material_type: str
    status: str


class WarehouseCreate(BaseModel):
    """Create warehouse payload."""

    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=128)
    is_default: bool = False
    status: str = Field(default="active", max_length=16)


class WarehouseUpdate(BaseModel):
    """Patch warehouse payload."""

    name: str | None = Field(default=None, max_length=128)
    is_default: bool | None = None
    status: str | None = Field(default=None, max_length=16)


class WarehouseOut(BaseModel):
    """Warehouse response row."""

    id: int
    company_id: int
    code: str
    name: str
    is_default: bool
    status: str


__all__ = [
    "PageMeta",
    "CurrencyCreate",
    "CurrencyOut",
    "CustomerCreate",
    "CustomerUpdate",
    "CustomerOut",
    "SupplierCreate",
    "SupplierUpdate",
    "SupplierOut",
    "MaterialCreate",
    "MaterialUpdate",
    "MaterialOut",
    "WarehouseCreate",
    "WarehouseUpdate",
    "WarehouseOut",
]
