"""Application bootstrap helpers for schema initialization, migrations, and demo data seeding."""

import logging

from app.core.errors import ConfigurationError
from app.core.settings import Settings
from app.db.models import Position, TradeOrder
from app.db.session import Base, engine
from app.domain.reconciliation import ReconciliationRunRecord, ReconciliationStatus
from app.domain.trading import OrderStatus, PositionRecord, PositionSide, SignalAction, StrategyRunRecord, TradeAuditRecord, TradeLifecycleStatus, TradeOrderRecord
from app.repositories.reconciliation_repository import ReconciliationRepository
from app.repositories.trade_audit_repository import TradeAuditRepository
from app.repositories.trading_repository import PositionRepository, StrategyRunRepository, TradeOrderRepository
from app.repositories.user_repository import UserRepository
from app.security.tokens import PasswordManager

logger = logging.getLogger(__name__)

try:
    from alembic import command
    from alembic.config import Config
except Exception:
    command = None
    Config = None


def initialize_database_schema(settings: Settings) -> str:
    """Apply migrations when configured, otherwise fall back to metadata bootstrap for local convenience."""
    if settings.run_migrations_on_start:
        if not command or not Config:
            raise ConfigurationError("RUN_MIGRATIONS_ON_START is enabled, but Alembic is unavailable.")
        alembic_config = Config("alembic.ini")
        command.upgrade(alembic_config, "head")
        logger.info("Database migrations applied during startup")
        return "migrations"

    is_local_mode = settings.environment.lower() in {"development", "local"}
    if settings.bootstrap_schema:
        if not is_local_mode:
            logger.warning("BOOTSTRAP_SCHEMA is enabled outside local/development mode; consider using migrations instead.")
        Base.metadata.create_all(bind=engine)
        logger.info("Database schema bootstrapped from SQLAlchemy metadata")
        return "metadata"

    if is_local_mode:
        logger.info("Database bootstrap skipped by configuration")
        return "skipped"

    raise ConfigurationError("No startup schema strategy is enabled. Configure migrations or bootstrap for this environment.")


def seed_demo_data(settings: Settings, session) -> bool:
    """Insert a small demo dataset and local users once so the template is usable immediately."""
    user_repository = UserRepository(session)
    _ensure_local_user(user_repository, username="trader", password="trader123", role="TRADER")
    _ensure_local_user(user_repository, username="operator", password="operator123", role="OPERATOR")
    _ensure_local_user(user_repository, username="admin", password="admin123", role="ADMIN")

    if not settings.seed_demo_data:
        return False
    if session.query(TradeOrder).count() > 0 or session.query(Position).count() > 0:
        logger.info("Demo data skipped because trading records already exist")
        return False

    audit_repository = TradeAuditRepository(session)
    strategy_run_repository = StrategyRunRepository(session)
    trade_order_repository = TradeOrderRepository(session)
    position_repository = PositionRepository(session)
    reconciliation_repository = ReconciliationRepository(session)

    audit_repository.create_audit_log(TradeAuditRecord(symbol="AAPL", status=TradeLifecycleStatus.EXECUTED, detail="Seeded demo trade executed successfully.", metadata={"seeded": True}))
    strategy_run_repository.create_strategy_run(StrategyRunRecord(symbol="AAPL", timeframe="1Min", short_window=5, long_window=20, action=SignalAction.BUY, confidence=0.81, reason="Seeded moving-average crossover example.", metadata={"seeded": True}))
    trade_order_repository.create_trade_order(TradeOrderRecord(symbol="AAPL", action=SignalAction.BUY, quantity=10, status=OrderStatus.SIMULATED, requested_price=189.42, broker_order_id=None, dry_run=True, metadata={"seeded": True}))
    position_repository.upsert_position(PositionRecord(symbol="AAPL", side=PositionSide.LONG, quantity=10, average_price=189.42, metadata={"seeded": True}))
    reconciliation_repository.create_reconciliation_run(ReconciliationRunRecord(status=ReconciliationStatus.MATCHED, source="paper", checked_symbols=1, mismatched_symbols=0, detail="Seeded reconciliation example.", metadata={"seeded": True, "items": []}))
    logger.info("Demo data seeded successfully")
    return True


def _ensure_local_user(user_repository: UserRepository, username: str, password: str, role: str) -> None:
    """Create a default local user when it does not already exist so the template has working login credentials."""
    if user_repository.get_by_username(username) is None:
        user_repository.create_user(username=username, password_hash=PasswordManager.hash_password(password), role=role)
        logger.info("Local template user created", extra={"username": username, "role": role})
