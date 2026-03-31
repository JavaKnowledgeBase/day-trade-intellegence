"""Dependency factory functions used by FastAPI routes and background workers."""

from collections.abc import Generator

from sqlalchemy.orm import Session

from app.core.settings import get_settings
from app.db.session import SessionLocal
from app.repositories.reconciliation_repository import ReconciliationRepository
from app.repositories.trade_audit_repository import TradeAuditRepository
from app.repositories.trading_repository import PositionRepository, StrategyRunRepository, TradeOrderRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.execution_service import ExecutionService
from app.services.market_data_service import MarketDataService
from app.services.operational_service import OperationalStatusService
from app.services.orchestrator import TradingOrchestrator
from app.services.portfolio_service import PortfolioService
from app.services.query_service import TradingQueryService
from app.services.reconciliation_service import ReconciliationService
from app.services.risk_manager import RiskManager
from app.services.strategy_engine import StrategyEngine


def get_db_session() -> Generator[Session, None, None]:
    """Create a short-lived SQLAlchemy session for one API request and close it afterwards."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_trading_orchestrator(session: Session) -> TradingOrchestrator:
    """Wire together the services and repositories required by the trading endpoint in one place."""
    settings = get_settings()
    return TradingOrchestrator(
        market_data_service=MarketDataService(settings),
        strategy_engine=StrategyEngine(),
        risk_manager=RiskManager(settings),
        execution_service=ExecutionService(settings),
        portfolio_service=PortfolioService(settings),
        audit_repository=TradeAuditRepository(session),
        strategy_run_repository=StrategyRunRepository(session),
        trade_order_repository=TradeOrderRepository(session),
        position_repository=PositionRepository(session),
    )


def get_query_service(session: Session) -> TradingQueryService:
    """Build the read-oriented query service used by operator-facing reporting endpoints."""
    return TradingQueryService(
        audit_repository=TradeAuditRepository(session),
        strategy_run_repository=StrategyRunRepository(session),
        trade_order_repository=TradeOrderRepository(session),
        position_repository=PositionRepository(session),
        reconciliation_repository=ReconciliationRepository(session),
    )


def get_portfolio_service() -> PortfolioService:
    """Build the portfolio service used to expose live or synthetic account state."""
    return PortfolioService(get_settings())


def get_reconciliation_service(session: Session) -> ReconciliationService:
    """Build the reconciliation service used by manual and background sync workflows."""
    settings = get_settings()
    query_service = TradingQueryService(
        audit_repository=TradeAuditRepository(session),
        strategy_run_repository=StrategyRunRepository(session),
        trade_order_repository=TradeOrderRepository(session),
        position_repository=PositionRepository(session),
        reconciliation_repository=ReconciliationRepository(session),
    )
    return ReconciliationService(
        portfolio_service=PortfolioService(settings),
        query_service=query_service,
        reconciliation_repository=ReconciliationRepository(session),
    )


def get_operational_status_service() -> OperationalStatusService:
    """Build the operational status service used by readiness and admin system endpoints."""
    return OperationalStatusService(get_settings())


def get_auth_service(session: Session) -> AuthService:
    """Build the auth service used by login and current-user endpoints."""
    return AuthService(get_settings(), UserRepository(session))
