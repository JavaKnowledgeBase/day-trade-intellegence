"""Tests for the read-oriented query and portfolio services."""

import asyncio
from datetime import datetime, timezone

from app.db.models import Position, ReconciliationRun, StrategyRun, TradeAuditLog, TradeOrder
from app.services.portfolio_service import PortfolioService
from app.services.query_service import TradingQueryService


class FakeAuditRepository:
    """Return in-memory audit data without requiring a database connection."""

    def list_audit_logs(self, symbol: str | None, limit: int, offset: int):
        item = TradeAuditLog(id=1, symbol="AAPL", status="EXECUTED", detail="ok", metadata_json={"stage": "execution"}, created_at=datetime.now(timezone.utc))
        return 1, [item]


class FakeStrategyRunRepository:
    """Return in-memory strategy-run data without requiring a database connection."""

    def list_strategy_runs(self, symbol: str | None, limit: int, offset: int):
        item = StrategyRun(id=1, symbol="AAPL", timeframe="1Min", short_window=5, long_window=20, action="BUY", confidence=0.8, reason="test", metadata_json={"x": 1}, created_at=datetime.now(timezone.utc))
        return 1, [item]


class FakeTradeOrderRepository:
    """Return in-memory order data without requiring a database connection."""

    def list_trade_orders(self, symbol: str | None, limit: int, offset: int):
        item = TradeOrder(id=1, symbol="AAPL", action="BUY", quantity=1, status="SIMULATED", requested_price=100.0, broker_order_id=None, dry_run=True, metadata_json={"y": 2}, created_at=datetime.now(timezone.utc))
        return 1, [item]


class FakePositionRepository:
    """Return in-memory position data without requiring a database connection."""

    def list_positions(self, symbol: str | None):
        item = Position(id=1, symbol="AAPL", side="LONG", quantity=1, average_price=100.0, metadata_json={"z": 3}, updated_at=datetime.now(timezone.utc))
        return 1, [item]


class FakeReconciliationRepository:
    """Return in-memory reconciliation data without requiring a database connection."""

    def list_reconciliation_runs(self, limit: int, offset: int):
        item = ReconciliationRun(id=1, status="MATCHED", source="ibkr", checked_symbols=1, mismatched_symbols=0, detail="ok", metadata_json={"items": []}, created_at=datetime.now(timezone.utc))
        return 1, [item]


class FakeSettings:
    """Provide only the settings attributes needed by the paper portfolio service during tests."""

    paper_account_equity = 100000.0
    paper_buying_power = 250000.0
    ibkr_host = "127.0.0.1"
    ibkr_port = 7497
    ibkr_client_id = 1


def test_query_service_maps_repository_results() -> None:
    """Validate that the query service converts repository objects into API response models."""
    service = TradingQueryService(FakeAuditRepository(), FakeStrategyRunRepository(), FakeTradeOrderRepository(), FakePositionRepository(), FakeReconciliationRepository())
    assert service.list_trade_orders(symbol=None, limit=50, offset=0).total == 1
    assert service.list_positions(symbol=None).total == 1
    assert service.list_strategy_runs(symbol=None, limit=50, offset=0).total == 1
    assert service.list_audit_logs(symbol=None, limit=50, offset=0).total == 1
    assert service.list_reconciliation_runs(limit=50, offset=0).total == 1


def test_portfolio_service_returns_paper_snapshot() -> None:
    """Validate that the portfolio service produces a safe synthetic snapshot when live access is disabled."""
    service = PortfolioService(FakeSettings())
    snapshot = asyncio.run(service.get_portfolio_snapshot(use_live_data=False))
    assert snapshot.source == "paper"
    assert snapshot.net_liquidation == 100000.0
