"""Tests for local market-data fallback behavior."""

import asyncio

from app.core.settings import Settings
from app.services.market_data_service import MarketDataService


def test_market_data_service_returns_synthetic_bars_in_development_without_credentials() -> None:
    """Validate that local development can still exercise trading flows without Alpaca credentials."""
    service = MarketDataService(
        Settings(
            ENVIRONMENT="development",
            ALPACA_API_KEY="",
            ALPACA_SECRET_KEY="",
        )
    )

    bars = asyncio.run(service.get_recent_bars(symbol="AAPL", timeframe="1Min", limit=4))

    assert len(bars) == 4
    assert bars[-1].close > bars[0].close
    assert all(bar.timestamp for bar in bars)
