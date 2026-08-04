"""Master-data APIs: currencies, customers, suppliers, materials, warehouses."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, require_permissions
from app.core.response import ok
from app.db.session import get_db
from app.modules.master import services
from app.modules.master.schemas import (
    CurrencyCreate,
    CustomerCreate,
    CustomerUpdate,
    MaterialCreate,
    MaterialUpdate,
    SupplierCreate,
    SupplierUpdate,
    WarehouseCreate,
    WarehouseUpdate,
)

router = APIRouter(prefix="/master", tags=["master"])


@router.get("/currencies")
def list_currencies(
    _ctx: Annotated[AuthContext, Depends(require_permissions("master.read"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """List currencies."""
    return ok([i.model_dump() for i in services.list_currencies(db)])


@router.post("/currencies")
def create_currency(
    body: CurrencyCreate,
    ctx: Annotated[AuthContext, Depends(require_permissions("master.write"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Create currency (admin/write)."""
    return ok(services.create_currency(db, body, ctx.user.id).model_dump())


@router.get("/customers")
def list_customers(
    ctx: Annotated[AuthContext, Depends(require_permissions("master.read"))],
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> dict:
    """List customers in active company."""
    data = services.list_customers(db, ctx.company_id, page=page, page_size=page_size)
    return ok(
        {
            "items": [i.model_dump(mode="json") for i in data["items"]],
            "meta": data["meta"].model_dump(),
        }
    )


@router.post("/customers")
def create_customer(
    body: CustomerCreate,
    ctx: Annotated[AuthContext, Depends(require_permissions("master.write"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Create customer."""
    return ok(
        services.create_customer(db, ctx.company_id, body, ctx.user.id).model_dump(
            mode="json"
        )
    )


@router.get("/customers/{customer_id}")
def get_customer(
    customer_id: int,
    ctx: Annotated[AuthContext, Depends(require_permissions("master.read"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Get customer detail."""
    return ok(
        services.get_customer(db, ctx.company_id, customer_id).model_dump(mode="json")
    )


@router.patch("/customers/{customer_id}")
def update_customer(
    customer_id: int,
    body: CustomerUpdate,
    ctx: Annotated[AuthContext, Depends(require_permissions("master.write"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Update customer."""
    return ok(
        services.update_customer(
            db, ctx.company_id, customer_id, body, ctx.user.id
        ).model_dump(mode="json")
    )


@router.delete("/customers/{customer_id}")
def delete_customer(
    customer_id: int,
    ctx: Annotated[AuthContext, Depends(require_permissions("master.write"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Soft-delete customer (inactive)."""
    services.delete_customer(db, ctx.company_id, customer_id, ctx.user.id)
    return ok({"id": customer_id, "status": "inactive"})


@router.get("/suppliers")
def list_suppliers(
    ctx: Annotated[AuthContext, Depends(require_permissions("master.read"))],
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> dict:
    """List suppliers."""
    data = services.list_suppliers(db, ctx.company_id, page=page, page_size=page_size)
    return ok(
        {
            "items": [i.model_dump() for i in data["items"]],
            "meta": data["meta"].model_dump(),
        }
    )


@router.post("/suppliers")
def create_supplier(
    body: SupplierCreate,
    ctx: Annotated[AuthContext, Depends(require_permissions("master.write"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Create supplier."""
    return ok(services.create_supplier(db, ctx.company_id, body, ctx.user.id).model_dump())


@router.get("/suppliers/{supplier_id}")
def get_supplier(
    supplier_id: int,
    ctx: Annotated[AuthContext, Depends(require_permissions("master.read"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Get supplier detail."""
    return ok(services.get_supplier(db, ctx.company_id, supplier_id).model_dump())


@router.patch("/suppliers/{supplier_id}")
def update_supplier(
    supplier_id: int,
    body: SupplierUpdate,
    ctx: Annotated[AuthContext, Depends(require_permissions("master.write"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Update supplier."""
    return ok(
        services.update_supplier(
            db, ctx.company_id, supplier_id, body, ctx.user.id
        ).model_dump()
    )


@router.delete("/suppliers/{supplier_id}")
def delete_supplier(
    supplier_id: int,
    ctx: Annotated[AuthContext, Depends(require_permissions("master.write"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Soft-delete supplier."""
    services.delete_supplier(db, ctx.company_id, supplier_id, ctx.user.id)
    return ok({"id": supplier_id, "status": "inactive"})


@router.get("/materials")
def list_materials(
    ctx: Annotated[AuthContext, Depends(require_permissions("master.read"))],
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> dict:
    """List materials."""
    data = services.list_materials(db, ctx.company_id, page=page, page_size=page_size)
    return ok(
        {
            "items": [i.model_dump() for i in data["items"]],
            "meta": data["meta"].model_dump(),
        }
    )


@router.post("/materials")
def create_material(
    body: MaterialCreate,
    ctx: Annotated[AuthContext, Depends(require_permissions("master.write"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Create material."""
    return ok(services.create_material(db, ctx.company_id, body, ctx.user.id).model_dump())


@router.get("/materials/{material_id}")
def get_material(
    material_id: int,
    ctx: Annotated[AuthContext, Depends(require_permissions("master.read"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Get material detail."""
    return ok(services.get_material(db, ctx.company_id, material_id).model_dump())


@router.patch("/materials/{material_id}")
def update_material(
    material_id: int,
    body: MaterialUpdate,
    ctx: Annotated[AuthContext, Depends(require_permissions("master.write"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Update material."""
    return ok(
        services.update_material(
            db, ctx.company_id, material_id, body, ctx.user.id
        ).model_dump()
    )


@router.delete("/materials/{material_id}")
def delete_material(
    material_id: int,
    ctx: Annotated[AuthContext, Depends(require_permissions("master.write"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Soft-delete material."""
    services.delete_material(db, ctx.company_id, material_id, ctx.user.id)
    return ok({"id": material_id, "status": "inactive"})


@router.get("/warehouses")
def list_warehouses(
    ctx: Annotated[AuthContext, Depends(require_permissions("master.read"))],
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> dict:
    """List warehouses."""
    data = services.list_warehouses(db, ctx.company_id, page=page, page_size=page_size)
    return ok(
        {
            "items": [i.model_dump() for i in data["items"]],
            "meta": data["meta"].model_dump(),
        }
    )


@router.post("/warehouses")
def create_warehouse(
    body: WarehouseCreate,
    ctx: Annotated[AuthContext, Depends(require_permissions("master.write"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Create warehouse."""
    return ok(
        services.create_warehouse(db, ctx.company_id, body, ctx.user.id).model_dump()
    )


@router.get("/warehouses/{warehouse_id}")
def get_warehouse(
    warehouse_id: int,
    ctx: Annotated[AuthContext, Depends(require_permissions("master.read"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Get warehouse detail."""
    return ok(services.get_warehouse(db, ctx.company_id, warehouse_id).model_dump())


@router.patch("/warehouses/{warehouse_id}")
def update_warehouse(
    warehouse_id: int,
    body: WarehouseUpdate,
    ctx: Annotated[AuthContext, Depends(require_permissions("master.write"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Update warehouse."""
    return ok(
        services.update_warehouse(
            db, ctx.company_id, warehouse_id, body, ctx.user.id
        ).model_dump()
    )
