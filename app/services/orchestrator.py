"""Orchestration service that coordinates market data, strategy, risk, execution, and persistence."""

import logging

from app.domain.trading import OrderStatus, PositionRecord, PositionSide, StrategyRunRecord, TradeAuditRecord, TradeLifecycleStatus, TradeOrderRecord, TradeSignalRequest, TradeSignalResponse
from app.repositories.trade_audit_repository import TradeAuditRepository
from app.repositories.trading_repository import PositionRepository, StrategyRunRepository, TradeOrderRepository
from app.services.execution_service import ExecutionService
from app.services.market_data_service import MarketDataService
from app.services.portfolio_service import PortfolioService
from app.services.risk_manager import RiskManager
from app.services.strategy_engine import StrategyEngine

logger = logging.getLogger(__name__)


class TradingOrchestrator:
    """Coordinate the full trading workflow from market-data lookup through execution and persistence."""

    def __init__(self, market_data_service: MarketDataService, strategy_engine: StrategyEngine, risk_manager: RiskManager, execution_service: ExecutionService, portfolio_service: PortfolioService, audit_repository: TradeAuditRepository, strategy_run_repository: StrategyRunRepository, trade_order_repository: TradeOrderRepository, position_repository: PositionRepository) -> None:
        """Store the collaborating services and repositories used by the trading application layer."""
        self.market_data_service = market_data_service
        self.strategy_engine = strategy_engine
        self.risk_manager = risk_manager
        self.execution_service = execution_service
        self.portfolio_service = portfolio_service
        self.audit_repository = audit_repository
        self.strategy_run_repository = strategy_run_repository
        self.trade_order_repository = trade_order_repository
        self.position_repository = position_repository

    def _record_audit_event(self, record: TradeAuditRecord) -> None:
        """Persist an audit event while preventing audit-write failures from obscuring the primary trade flow."""
        try:
            self.audit_repository.create_audit_log(record)
        except Exception:
            logger.exception("Failed to persist trade audit event", extra={"symbol": record.symbol, "status": record.status.value})

    def _record_strategy_run(self, record: StrategyRunRecord) -> None:
        """Persist the normalized strategy decision for later analytics and replay."""
        try:
            self.strategy_run_repository.create_strategy_run(record)
        except Exception:
            logger.exception("Failed to persist strategy run", extra={"symbol": record.symbol})

    def _record_trade_order(self, record: TradeOrderRecord) -> None:
        """Persist the generated order record so operations teams can inspect order history."""
        try:
            self.trade_order_repository.create_trade_order(record)
        except Exception:
            logger.exception("Failed to persist trade order", extra={"symbol": record.symbol, "status": record.status.value})

    def _upsert_position(self, record: PositionRecord) -> None:
        """Persist the internal position snapshot so future services can reconcile exposure."""
        try:
            self.position_repository.upsert_position(record)
        except Exception:
            logger.exception("Failed to persist position", extra={"symbol": record.symbol})

    async def process_signal(self, request: TradeSignalRequest) -> TradeSignalResponse:
        """Run data fetch, strategy evaluation, live-account-aware risk checks, execution, and persistence."""
        logger.info("Processing trade signal request", extra={"symbol": request.symbol, "dry_run": request.dry_run})
        self._record_audit_event(TradeAuditRecord(symbol=request.symbol, status=TradeLifecycleStatus.RECEIVED, detail="Trade request received by orchestration layer.", metadata={"dry_run": request.dry_run, "quantity": request.quantity}))

        try:
            portfolio_snapshot = await self.portfolio_service.get_portfolio_snapshot(use_live_data=not request.dry_run)
            bars = await self.market_data_service.get_recent_bars(symbol=request.symbol, timeframe=request.timeframe, limit=request.long_window)
            decision = self.strategy_engine.evaluate_moving_average_crossover(symbol=request.symbol, bars=bars, short_window=request.short_window, long_window=request.long_window)
            self._record_strategy_run(StrategyRunRecord(symbol=request.symbol, timeframe=request.timeframe, short_window=request.short_window, long_window=request.long_window, action=decision.action, confidence=decision.confidence, reason=decision.reason, metadata=decision.metadata))
            self._record_audit_event(TradeAuditRecord(symbol=request.symbol, status=TradeLifecycleStatus.STRATEGY_EVALUATED, detail="Strategy evaluation completed.", metadata={"action": decision.action.value, "confidence": decision.confidence}))

            latest_price = bars[-1].close
            risk_approved = self.risk_manager.validate_trade(symbol=request.symbol, decision=decision, quantity=request.quantity, reference_price=latest_price, account_equity=portfolio_snapshot.net_liquidation, current_drawdown_pct=portfolio_snapshot.drawdown_pct)
            self._record_audit_event(TradeAuditRecord(symbol=request.symbol, status=TradeLifecycleStatus.RISK_APPROVED, detail="Trade passed risk validation.", metadata={"latest_price": latest_price, "risk_approved": risk_approved, "account_equity": portfolio_snapshot.net_liquidation, "drawdown_pct": portfolio_snapshot.drawdown_pct}))

            execution_result = await self.execution_service.execute_order(symbol=request.symbol, action=decision.action, quantity=request.quantity, dry_run=request.dry_run)
            order_status = OrderStatus.SIMULATED if execution_result.status == "simulated" else OrderStatus.SUBMITTED
            self._record_trade_order(TradeOrderRecord(symbol=request.symbol, action=decision.action, quantity=request.quantity, status=order_status, requested_price=latest_price, broker_order_id=execution_result.broker_order_id, dry_run=request.dry_run, metadata={"execution_message": execution_result.message, "account_source": portfolio_snapshot.source}))
            self._upsert_position(PositionRecord(symbol=request.symbol, side=PositionSide.LONG if decision.action.value == "BUY" else PositionSide.SHORT, quantity=request.quantity, average_price=latest_price, metadata={"source": "trading_orchestrator", "dry_run": request.dry_run}))
            self._record_audit_event(TradeAuditRecord(symbol=request.symbol, status=TradeLifecycleStatus.EXECUTED, detail="Execution step completed.", metadata={"execution_status": execution_result.status, "broker_order_id": execution_result.broker_order_id}))

            logger.info("Trade signal request completed", extra={"symbol": request.symbol, "execution_status": execution_result.status})
            return TradeSignalResponse(symbol=request.symbol, decision=decision, risk_approved=risk_approved, execution=execution_result)
        except Exception as exc:
            self._record_audit_event(TradeAuditRecord(symbol=request.symbol, status=TradeLifecycleStatus.FAILED, detail="Trade workflow failed.", metadata={"error_type": exc.__class__.__name__, "message": str(exc)}))
            logger.exception("Trade signal request failed", extra={"symbol": request.symbol})
            raise
