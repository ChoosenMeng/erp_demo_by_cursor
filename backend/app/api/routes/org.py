"""Organization admin APIs: companies, users, roles, permissions."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, require_permissions
from app.core.response import ok
from app.db.session import get_db
from app.modules.org import services
from app.modules.org.schemas import (
    CompanyCreate,
    CompanyUpdate,
    RoleCreate,
    RolePermissionsUpdate,
    UserCreate,
    UserRolesUpdate,
    UserUpdate,
)

router = APIRouter(prefix="/org", tags=["org"])


@router.get("/companies")
def list_companies(
    _ctx: Annotated[AuthContext, Depends(require_permissions("org.company.read"))],
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> dict:
    """List companies (paginated)."""
    data = services.list_companies(db, page=page, page_size=page_size)
    return ok(
        {
            "items": [i.model_dump() for i in data["items"]],
            "meta": data["meta"].model_dump(),
        }
    )


@router.post("/companies")
def create_company(
    body: CompanyCreate,
    ctx: Annotated[AuthContext, Depends(require_permissions("org.company.write"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Create a company."""
    return ok(services.create_company(db, body, ctx.user.id).model_dump())


@router.get("/companies/{company_id}")
def get_company(
    company_id: int,
    _ctx: Annotated[AuthContext, Depends(require_permissions("org.company.read"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Get company detail."""
    return ok(services.get_company(db, company_id).model_dump())


@router.patch("/companies/{company_id}")
def update_company(
    company_id: int,
    body: CompanyUpdate,
    ctx: Annotated[AuthContext, Depends(require_permissions("org.company.write"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Update company fields."""
    return ok(services.update_company(db, company_id, body, ctx.user.id).model_dump())


@router.get("/users")
def list_users(
    _ctx: Annotated[AuthContext, Depends(require_permissions("org.user.read"))],
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> dict:
    """List users (paginated)."""
    data = services.list_users(db, page=page, page_size=page_size)
    return ok(
        {
            "items": [i.model_dump() for i in data["items"]],
            "meta": data["meta"].model_dump(),
        }
    )


@router.post("/users")
def create_user(
    body: UserCreate,
    ctx: Annotated[AuthContext, Depends(require_permissions("org.user.write"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Create user with optional roles/companies."""
    return ok(services.create_user(db, body, ctx.user.id).model_dump())


@router.get("/users/{user_id}")
def get_user(
    user_id: int,
    _ctx: Annotated[AuthContext, Depends(require_permissions("org.user.read"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Get user detail."""
    return ok(services.get_user(db, user_id).model_dump())


@router.patch("/users/{user_id}")
def update_user(
    user_id: int,
    body: UserUpdate,
    ctx: Annotated[AuthContext, Depends(require_permissions("org.user.write"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Update user profile/status/password."""
    return ok(services.update_user(db, user_id, body, ctx.user.id).model_dump())


@router.put("/users/{user_id}/roles")
def set_user_roles(
    user_id: int,
    body: UserRolesUpdate,
    ctx: Annotated[AuthContext, Depends(require_permissions("org.user.write"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Replace roles bound to a user."""
    return ok(services.set_user_roles(db, user_id, body.role_ids, ctx.user.id).model_dump())


@router.get("/roles")
def list_roles(
    _ctx: Annotated[AuthContext, Depends(require_permissions("org.role.read"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """List roles with permission codes."""
    return ok([r.model_dump() for r in services.list_roles(db)])


@router.post("/roles")
def create_role(
    body: RoleCreate,
    ctx: Annotated[AuthContext, Depends(require_permissions("org.role.write"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Create a role."""
    return ok(services.create_role(db, body, ctx.user.id).model_dump())


@router.put("/roles/{role_id}/permissions")
def set_role_permissions(
    role_id: int,
    body: RolePermissionsUpdate,
    ctx: Annotated[AuthContext, Depends(require_permissions("org.role.write"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Replace permissions bound to a role."""
    return ok(
        services.set_role_permissions(db, role_id, body.permission_ids, ctx.user.id).model_dump()
    )


@router.get("/permissions")
def list_permissions(
    _ctx: Annotated[AuthContext, Depends(require_permissions("org.role.read"))],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """List all permission points."""
    return ok([p.model_dump() for p in services.list_permissions(db)])
