"""Portfolio endpoints that expose current account state for operators and risk-aware workflows."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import get_portfolio_service
from app.domain.portfolio import PortfolioSnapshot
from app.security.auth import UserRole, require_role
from app.services.portfolio_service import PortfolioService

router = APIRouter()


@router.get("/summary", response_model=PortfolioSnapshot, status_code=status.HTTP_200_OK)
async def get_portfolio_summary(
    _: Annotated[UserRole, Depends(require_role({UserRole.OPERATOR, UserRole.ADMIN}))],
    live: bool = Query(default=False),
    portfolio_service: PortfolioService = Depends(get_portfolio_service),
) -> PortfolioSnapshot:
    """Return either a safe synthetic paper snapshot or a live IBKR-backed account summary."""
    return await portfolio_service.get_portfolio_snapshot(use_live_data=live)
