"""Tests for the main orchestration workflow."""

import asyncio
from datetime import datetime, timezone

from app.domain.portfolio import PortfolioSnapshot
from app.domain.trading import ExecutionResult, MarketBar, SignalAction, StrategyDecision, TradeSignalRequest
from app.services.orchestrator import TradingOrchestrator


class FakeMarketDataService:
    """Return deterministic bars so tests stay fast and independent from Alpaca."""

    async def get_recent_bars(self, symbol: str, timeframe: str, limit: int) -> list[MarketBar]:
        return [
            MarketBar(close=100.0, timestamp="2026-01-01T09:30:00Z"),
            MarketBar(close=101.0, timestamp="2026-01-01T09:31:00Z"),
            MarketBar(close=102.0, timestamp="2026-01-01T09:32:00Z"),
            MarketBar(close=103.0, timestamp="2026-01-01T09:33:00Z"),
        ]


class FakeStrategyEngine:
    """Return a stable buy decision so the test focuses on orchestration wiring."""

    def evaluate_moving_average_crossover(self, symbol: str, bars: list[MarketBar], short_window: int, long_window: int) -> StrategyDecision:
        return StrategyDecision(action=SignalAction.BUY, confidence=0.82, reason="Synthetic buy signal for orchestration testing.", metadata={"test": True})


class FakeRiskManager:
    """Approve all trades so the test does not depend on risk policy thresholds."""

    def validate_trade(self, symbol: str, decision: StrategyDecision, quantity: int, reference_price: float, account_equity: float, current_drawdown_pct: float) -> bool:
        return True


class FakeExecutionService:
    """Return a simulated execution result without touching a real broker connection."""

    async def execute_order(self, symbol: str, action: SignalAction, quantity: int, dry_run: bool) -> ExecutionResult:
        return ExecutionResult(status="simulated", broker_order_id=None, message="Synthetic execution for tests.")


class FakePortfolioService:
    """Return a stable portfolio snapshot so orchestration tests can exercise live-risk wiring safely."""

    async def get_portfolio_snapshot(self, use_live_data: bool) -> PortfolioSnapshot:
        return PortfolioSnapshot(account_id="paper", source="paper", net_liquidation=100000.0, available_funds=100000.0, buying_power=250000.0, drawdown_pct=0.0, positions=[], as_of=datetime.now(timezone.utc))


class FakeAuditRepository:
    """Capture audit events in memory so tests can verify orchestration side effects."""

    def __init__(self) -> None:
        self.records = []

    def create_audit_log(self, record) -> None:
        self.records.append(record)


class FakeStrategyRunRepository:
    """Capture persisted strategy runs in memory for orchestration tests."""

    def __init__(self) -> None:
        self.records = []

    def create_strategy_run(self, record) -> None:
        self.records.append(record)


class FakeTradeOrderRepository:
    """Capture persisted trade orders in memory for orchestration tests."""

    def __init__(self) -> None:
        self.records = []

    def create_trade_order(self, record) -> None:
        self.records.append(record)


class FakePositionRepository:
    """Capture position upserts in memory for orchestration tests."""

    def __init__(self) -> None:
        self.records = []

    def upsert_position(self, record) -> None:
        self.records.append(record)


def test_orchestrator_process_signal() -> None:
    """Validate that the orchestrator returns the expected combined trading response and persistence side effects."""
    audit_repository = FakeAuditRepository()
    strategy_run_repository = FakeStrategyRunRepository()
    trade_order_repository = FakeTradeOrderRepository()
    position_repository = FakePositionRepository()
    orchestrator = TradingOrchestrator(
        FakeMarketDataService(),
        FakeStrategyEngine(),
        FakeRiskManager(),
        FakeExecutionService(),
        FakePortfolioService(),
        audit_repository,
        strategy_run_repository,
        trade_order_repository,
        position_repository,
    )
    request = TradeSignalRequest(symbol="AAPL", short_window=2, long_window=4, quantity=1)
    response = asyncio.run(orchestrator.process_signal(request))
    assert response.symbol == "AAPL"
    assert response.decision.action == SignalAction.BUY
    assert response.risk_approved is True
    assert response.execution.status == "simulated"
    assert len(audit_repository.records) == 4
    assert len(strategy_run_repository.records) == 1
    assert len(trade_order_repository.records) == 1
    assert len(position_repository.records) == 1
