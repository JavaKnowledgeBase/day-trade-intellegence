"""Trading endpoints that expose strategy evaluation, order history, positions, and audit views."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db_session, get_query_service, get_trading_orchestrator
from app.domain.trading import PositionListResponse, StrategyRunListResponse, TradeAuditLogListResponse, TradeOrderListResponse, TradeSignalRequest, TradeSignalResponse
from app.security.auth import UserRole, require_role
from app.services.orchestrator import TradingOrchestrator
from app.services.query_service import TradingQueryService

router = APIRouter()


@router.post("/signal", response_model=TradeSignalResponse, status_code=status.HTTP_200_OK)
async def generate_and_execute_signal(
    request: TradeSignalRequest,
    session: Annotated[Session, Depends(get_db_session)],
    _: Annotated[UserRole, Depends(require_role({UserRole.TRADER, UserRole.OPERATOR, UserRole.ADMIN}))],
) -> TradeSignalResponse:
    """Run the full trading workflow for a symbol and return the normalized result."""
    orchestrator: TradingOrchestrator = get_trading_orchestrator(session)
    return await orchestrator.process_signal(request)


@router.get("/orders", response_model=TradeOrderListResponse, status_code=status.HTTP_200_OK)
def list_trade_orders(
    session: Annotated[Session, Depends(get_db_session)],
    _: Annotated[UserRole, Depends(require_role({UserRole.OPERATOR, UserRole.ADMIN}))],
    symbol: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> TradeOrderListResponse:
    """Return paginated order history so operators can inspect broker or paper submissions."""
    query_service: TradingQueryService = get_query_service(session)
    return query_service.list_trade_orders(symbol=symbol, limit=limit, offset=offset)


@router.get("/positions", response_model=PositionListResponse, status_code=status.HTTP_200_OK)
def list_positions(
    session: Annotated[Session, Depends(get_db_session)],
    _: Annotated[UserRole, Depends(require_role({UserRole.OPERATOR, UserRole.ADMIN}))],
    symbol: str | None = Query(default=None),
) -> PositionListResponse:
    """Return the internal position snapshot used by the platform for exposure tracking."""
    query_service: TradingQueryService = get_query_service(session)
    return query_service.list_positions(symbol=symbol)


@router.get("/strategy-runs", response_model=StrategyRunListResponse, status_code=status.HTTP_200_OK)
def list_strategy_runs(
    session: Annotated[Session, Depends(get_db_session)],
    _: Annotated[UserRole, Depends(require_role({UserRole.OPERATOR, UserRole.ADMIN}))],
    symbol: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> StrategyRunListResponse:
    """Return paginated strategy evaluation history for analytics and debugging."""
    query_service: TradingQueryService = get_query_service(session)
    return query_service.list_strategy_runs(symbol=symbol, limit=limit, offset=offset)


@router.get("/audit-logs", response_model=TradeAuditLogListResponse, status_code=status.HTTP_200_OK)
def list_audit_logs(
    session: Annotated[Session, Depends(get_db_session)],
    _: Annotated[UserRole, Depends(require_role({UserRole.OPERATOR, UserRole.ADMIN}))],
    symbol: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> TradeAuditLogListResponse:
    """Return paginated lifecycle audit logs so operators can trace end-to-end trade processing."""
    query_service: TradingQueryService = get_query_service(session)
    return query_service.list_audit_logs(symbol=symbol, limit=limit, offset=offset)
