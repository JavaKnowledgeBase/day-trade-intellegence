"""API router composition for the FastAPI service."""

from fastapi import APIRouter

from app.api.routes import admin, auth, health, portfolio, reconciliation, trading

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(trading.router, prefix="/trading", tags=["trading"])
api_router.include_router(portfolio.router, prefix="/portfolio", tags=["portfolio"])
api_router.include_router(reconciliation.router, prefix="/reconciliation", tags=["reconciliation"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
