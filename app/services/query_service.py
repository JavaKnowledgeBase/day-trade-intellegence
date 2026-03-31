"""Service layer for operator-facing query APIs over persisted trading and reconciliation records."""

from app.domain.reconciliation import ReconciliationRunListResponse, ReconciliationRunRead
from app.domain.trading import PositionListResponse, PositionRead, StrategyRunListResponse, StrategyRunRead, TradeAuditLogListResponse, TradeAuditLogRead, TradeOrderListResponse, TradeOrderRead
from app.repositories.reconciliation_repository import ReconciliationRepository
from app.repositories.trade_audit_repository import TradeAuditRepository
from app.repositories.trading_repository import PositionRepository, StrategyRunRepository, TradeOrderRepository


class TradingQueryService:
    """Provide read-oriented responses for order history, positions, strategy runs, audit logs, and reconciliation history."""

    def __init__(self, audit_repository: TradeAuditRepository, strategy_run_repository: StrategyRunRepository, trade_order_repository: TradeOrderRepository, position_repository: PositionRepository, reconciliation_repository: ReconciliationRepository | None = None) -> None:
        """Store the repositories used to assemble operator-facing read models."""
        self.audit_repository = audit_repository
        self.strategy_run_repository = strategy_run_repository
        self.trade_order_repository = trade_order_repository
        self.position_repository = position_repository
        self.reconciliation_repository = reconciliation_repository

    def list_trade_orders(self, symbol: str | None, limit: int, offset: int) -> TradeOrderListResponse:
        """Return paginated order history with clean API models instead of ORM objects."""
        total, items = self.trade_order_repository.list_trade_orders(symbol=symbol, limit=limit, offset=offset)
        return TradeOrderListResponse(total=total, limit=limit, offset=offset, items=[TradeOrderRead(id=item.id, symbol=item.symbol, action=item.action, quantity=item.quantity, status=item.status, requested_price=item.requested_price, broker_order_id=item.broker_order_id, dry_run=item.dry_run, metadata=item.metadata_json, created_at=item.created_at) for item in items])

    def list_positions(self, symbol: str | None) -> PositionListResponse:
        """Return the current internal position snapshot for one symbol or the full book."""
        total, items = self.position_repository.list_positions(symbol=symbol)
        return PositionListResponse(total=total, items=[PositionRead(id=item.id, symbol=item.symbol, side=item.side, quantity=item.quantity, average_price=item.average_price, metadata=item.metadata_json, updated_at=item.updated_at) for item in items])

    def list_strategy_runs(self, symbol: str | None, limit: int, offset: int) -> StrategyRunListResponse:
        """Return paginated strategy-run history so operators can inspect signal generation."""
        total, items = self.strategy_run_repository.list_strategy_runs(symbol=symbol, limit=limit, offset=offset)
        return StrategyRunListResponse(total=total, limit=limit, offset=offset, items=[StrategyRunRead(id=item.id, symbol=item.symbol, timeframe=item.timeframe, short_window=item.short_window, long_window=item.long_window, action=item.action, confidence=item.confidence, reason=item.reason, metadata=item.metadata_json, created_at=item.created_at) for item in items])

    def list_audit_logs(self, symbol: str | None, limit: int, offset: int) -> TradeAuditLogListResponse:
        """Return paginated audit logs so operators can trace every trade lifecycle stage."""
        total, items = self.audit_repository.list_audit_logs(symbol=symbol, limit=limit, offset=offset)
        return TradeAuditLogListResponse(total=total, limit=limit, offset=offset, items=[TradeAuditLogRead(id=item.id, symbol=item.symbol, status=item.status, detail=item.detail, metadata=item.metadata_json, created_at=item.created_at) for item in items])

    def list_reconciliation_runs(self, limit: int, offset: int) -> ReconciliationRunListResponse:
        """Return paginated reconciliation history so operators can inspect sync health over time."""
        if self.reconciliation_repository is None:
            return ReconciliationRunListResponse(total=0, limit=limit, offset=offset, items=[])
        total, items = self.reconciliation_repository.list_reconciliation_runs(limit=limit, offset=offset)
        return ReconciliationRunListResponse(total=total, limit=limit, offset=offset, items=[ReconciliationRunRead(id=item.id, status=item.status, source=item.source, checked_symbols=item.checked_symbols, mismatched_symbols=item.mismatched_symbols, detail=item.detail, metadata=item.metadata_json, created_at=item.created_at) for item in items])
