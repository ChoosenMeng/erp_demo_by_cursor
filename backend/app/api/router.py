"""Aggregate versioned API routers."""

from fastapi import APIRouter

from app.api.routes import auth, health, inventory, master, org

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(org.router)
api_router.include_router(master.router)
api_router.include_router(inventory.router)
