"""Tests for the broker reconciliation workflow."""

import asyncio
from datetime import datetime, timezone

from app.domain.portfolio import BrokerPositionSnapshot, PortfolioSnapshot
from app.domain.trading import PositionListResponse, PositionRead
from app.services.reconciliation_service import ReconciliationService


class FakePortfolioService:
    """Return broker positions without touching a live IBKR connection."""

    async def get_portfolio_snapshot(self, use_live_data: bool = True) -> PortfolioSnapshot:
        return PortfolioSnapshot(
            account_id="ibkr",
            source="ibkr",
            net_liquidation=100000.0,
            available_funds=100000.0,
            buying_power=250000.0,
            drawdown_pct=0.0,
            positions=[BrokerPositionSnapshot(symbol="AAPL", quantity=2.0, market_price=101.0, market_value=202.0, average_cost=100.0)],
            as_of=datetime.now(timezone.utc),
        )


class FakeQueryService:
    """Return persisted internal positions without touching a database connection."""

    def list_positions(self, symbol: str | None) -> PositionListResponse:
        return PositionListResponse(total=1, items=[PositionRead(id=1, symbol="AAPL", side="LONG", quantity=1, average_price=100.0, metadata={}, updated_at=datetime.now(timezone.utc))])


class FakeReconciliationRepository:
    """Capture reconciliation runs in memory so tests can verify persistence side effects."""

    def __init__(self) -> None:
        self.records = []

    def create_reconciliation_run(self, record) -> None:
        self.records.append(record)


def test_reconciliation_detects_position_mismatch() -> None:
    """Validate that reconciliation marks a mismatch when broker and internal quantities differ."""
    repository = FakeReconciliationRepository()
    service = ReconciliationService(FakePortfolioService(), FakeQueryService(), repository)
    response = asyncio.run(service.reconcile_positions(use_live_data=True))
    assert response.status.value == "MISMATCHED"
    assert response.mismatched_symbols == 1
    assert len(repository.records) == 1
