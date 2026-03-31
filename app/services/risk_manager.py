"""Risk policy service used to approve or reject trade proposals."""

import logging

from app.core.errors import RiskViolationError
from app.core.settings import Settings
from app.domain.trading import SignalAction, StrategyDecision

logger = logging.getLogger(__name__)


class RiskManager:
    """Apply account-level risk controls before any trade is allowed to hit the broker."""

    def __init__(self, settings: Settings) -> None:
        """Store validated settings that define the system's default risk thresholds."""
        self.settings = settings

    def validate_trade(self, symbol: str, decision: StrategyDecision, quantity: int, reference_price: float, account_equity: float, current_drawdown_pct: float) -> bool:
        """Reject holds, cap position risk, check drawdown, and log approved trade proposals."""
        if decision.action == SignalAction.HOLD:
            raise RiskViolationError(f"{symbol} generated a HOLD signal, so no trade should be executed.")

        notional_value = quantity * reference_price
        capital_at_risk_pct = 0.0 if account_equity == 0 else notional_value / account_equity
        if capital_at_risk_pct > self.settings.max_capital_at_risk_pct:
            raise RiskViolationError(f"Trade exceeds capital at risk limit: {capital_at_risk_pct:.4f} > {self.settings.max_capital_at_risk_pct:.4f}.")
        if current_drawdown_pct > self.settings.max_drawdown_pct:
            raise RiskViolationError(f"Account drawdown {current_drawdown_pct:.4f} exceeds allowed threshold.")

        logger.info("Risk validation passed", extra={"symbol": symbol, "quantity": quantity, "reference_price": reference_price, "capital_at_risk_pct": capital_at_risk_pct, "account_equity": account_equity, "current_drawdown_pct": current_drawdown_pct})
        return True
