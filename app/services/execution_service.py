"""Execution adapter that submits orders to Interactive Brokers."""

from __future__ import annotations

import logging

from app.core.errors import ConfigurationError, ExecutionError
from app.core.settings import Settings
from app.domain.trading import ExecutionResult, SignalAction

logger = logging.getLogger(__name__)

try:
    from ib_insync import IB, MarketOrder, Stock
except Exception:
    IB = None
    MarketOrder = None
    Stock = None


class ExecutionService:
    """Send approved orders to IBKR or simulate them during development and paper trading."""

    def __init__(self, settings: Settings) -> None:
        """Store the broker connectivity settings used for live execution."""
        self.settings = settings

    async def execute_order(self, symbol: str, action: SignalAction, quantity: int, dry_run: bool) -> ExecutionResult:
        """Simulate or submit a market order, with structured logs and wrapped broker errors."""
        if action == SignalAction.HOLD:
            return ExecutionResult(status="skipped", broker_order_id=None, message="Execution skipped because the strategy returned HOLD.")
        if dry_run:
            logger.info("Dry-run execution completed", extra={"symbol": symbol, "action": action.value, "quantity": quantity})
            return ExecutionResult(status="simulated", broker_order_id=None, message="Dry run enabled. No live broker order was placed.")
        if not all([IB, MarketOrder, Stock]):
            raise ExecutionError("ib_insync components are unavailable in the current environment.")
        if not self.settings.ibkr_host or not self.settings.ibkr_port:
            raise ConfigurationError("IBKR connection settings are required for live execution.")

        ib = IB()
        try:
            ib.connect(self.settings.ibkr_host, self.settings.ibkr_port, clientId=self.settings.ibkr_client_id)
            contract = Stock(symbol, "SMART", "USD")
            order = MarketOrder(action.value, quantity)
            trade = ib.placeOrder(contract, order)
            ib.sleep(1)
            logger.info("Live order submitted", extra={"symbol": symbol, "action": action.value, "quantity": quantity})
            return ExecutionResult(status="submitted", broker_order_id=str(getattr(trade.order, "orderId", "")), message="Order submitted to Interactive Brokers.")
        except Exception as exc:
            logger.exception("Failed to execute broker order", extra={"symbol": symbol})
            raise ExecutionError(f"Unable to submit order for {symbol}.") from exc
        finally:
            if ib.isConnected():
                ib.disconnect()
