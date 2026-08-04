"""Aggregate versioned API routers."""

from fastapi import APIRouter

from app.api.routes import (
    auth,
    dashboard,
    finance,
    health,
    inventory,
    master,
    org,
    purchase,
    sales,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(org.router)
api_router.include_router(master.router)
api_router.include_router(inventory.router)
api_router.include_router(purchase.router)
api_router.include_router(sales.router)
api_router.include_router(finance.router)
api_router.include_router(dashboard.router)
