"""Service responsible for reading market data from Alpaca."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from app.core.errors import ConfigurationError, MarketDataError
from app.core.settings import Settings
from app.domain.trading import MarketBar

logger = logging.getLogger(__name__)

try:
    from alpaca.data.historical import StockHistoricalDataClient
    from alpaca.data.requests import StockBarsRequest
    from alpaca.data.timeframe import TimeFrame
except Exception:
    StockHistoricalDataClient = None
    StockBarsRequest = None
    TimeFrame = None


class MarketDataService:
    """Adapter around Alpaca market data APIs that converts provider responses into internal models."""

    def __init__(self, settings: Settings) -> None:
        """Store runtime settings needed to authenticate and tune data access."""
        self.settings = settings

    def _build_synthetic_bars(self, symbol: str, limit: int) -> list[MarketBar]:
        """Return deterministic demo bars so local environments remain usable without live credentials."""
        base_price = 100.0 + (sum(ord(char) for char in symbol.upper()) % 20)
        start = datetime.now(timezone.utc) - timedelta(minutes=max(limit - 1, 0))
        bars = []
        for index in range(limit):
            bars.append(
                MarketBar(
                    close=round(base_price + (index * 0.6), 2),
                    timestamp=(start + timedelta(minutes=index)).isoformat(),
                )
            )
        return bars

    async def get_recent_bars(self, symbol: str, timeframe: str, limit: int) -> list[MarketBar]:
        """Fetch recent bars from Alpaca, log the outcome, and raise domain errors on failure."""
        if not self.settings.alpaca_api_key or not self.settings.alpaca_secret_key:
            if self.settings.environment.lower() in {"development", "local"}:
                logger.warning(
                    "Using synthetic market bars because Alpaca credentials are not configured",
                    extra={"symbol": symbol, "timeframe": timeframe, "limit": limit},
                )
                return self._build_synthetic_bars(symbol=symbol, limit=limit)
            raise ConfigurationError("Alpaca API credentials are required for market data access.")
        if not all([StockHistoricalDataClient, StockBarsRequest, TimeFrame]):
            raise MarketDataError("alpaca-py components are unavailable in the current environment.")

        try:
            client = StockHistoricalDataClient(self.settings.alpaca_api_key, self.settings.alpaca_secret_key)
            request = StockBarsRequest(symbol_or_symbols=symbol, timeframe=TimeFrame.Minute, limit=limit, feed=self.settings.alpaca_data_feed)
            response = client.get_stock_bars(request)
            bars = response.data.get(symbol, [])
            logger.info("Fetched market bars", extra={"symbol": symbol, "timeframe": timeframe, "bars_returned": len(bars)})
            return [MarketBar(close=float(bar.close), timestamp=str(bar.timestamp)) for bar in bars]
        except Exception as exc:
            logger.exception("Failed to fetch market data", extra={"symbol": symbol})
            raise MarketDataError(f"Unable to retrieve market data for {symbol}.") from exc
