"""Trading strategy implementations and signal evaluation logic."""

from __future__ import annotations

import logging

from app.core.errors import StrategyError
from app.domain.trading import MarketBar, SignalAction, StrategyDecision

logger = logging.getLogger(__name__)


class StrategyEngine:
    """Evaluate trading signals using deterministic strategy rules that are easy to test and extend."""

    def evaluate_moving_average_crossover(self, symbol: str, bars: list[MarketBar], short_window: int, long_window: int) -> StrategyDecision:
        """Compare short and long moving averages to return a buy, sell, or hold decision."""
        if long_window <= short_window:
            raise StrategyError("The long moving average window must exceed the short window.")
        if len(bars) < long_window:
            raise StrategyError(f"Not enough bars to evaluate strategy. Required: {long_window}, received: {len(bars)}.")

        try:
            closes = [bar.close for bar in bars]
            short_average = sum(closes[-short_window:]) / short_window
            long_average = sum(closes[-long_window:]) / long_window
        except Exception as exc:
            raise StrategyError("Failed to calculate moving averages.") from exc

        if short_average > long_average:
            action = SignalAction.BUY
            reason = "Short moving average crossed above long moving average."
        elif short_average < long_average:
            action = SignalAction.SELL
            reason = "Short moving average fell below long moving average."
        else:
            action = SignalAction.HOLD
            reason = "Moving averages are equal, so no directional edge is present."

        gap = abs(short_average - long_average)
        confidence = min(gap / long_average, 1.0) if long_average else 0.0
        logger.info("Strategy evaluated", extra={"symbol": symbol, "action": action.value, "short_average": short_average, "long_average": long_average})
        return StrategyDecision(action=action, confidence=confidence, reason=reason, metadata={"short_average": short_average, "long_average": long_average})
