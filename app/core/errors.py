"""Custom exceptions and FastAPI exception handlers for predictable failures."""

import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class TradingPlatformError(Exception):
    """Base domain exception for business or integration failures across the platform."""


class ConfigurationError(TradingPlatformError):
    """Raised when a required runtime dependency or credential is missing."""


class MarketDataError(TradingPlatformError):
    """Raised when the market data provider cannot serve a request."""


class StrategyError(TradingPlatformError):
    """Raised when the strategy engine cannot evaluate a signal."""


class RiskViolationError(TradingPlatformError):
    """Raised when a proposed trade fails risk policy checks."""


class ExecutionError(TradingPlatformError):
    """Raised when broker order placement or confirmation fails."""


def register_exception_handlers(app: FastAPI) -> None:
    """Attach centralized exception handlers so API errors remain consistent and well logged."""

    @app.exception_handler(TradingPlatformError)
    async def handle_trading_error(request: Request, exc: TradingPlatformError) -> JSONResponse:
        logger.exception("Trading platform error occurred", extra={"path": str(request.url)})
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": str(exc), "error_type": exc.__class__.__name__})

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unexpected application error", extra={"path": str(request.url)})
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": "An unexpected internal error occurred."})
