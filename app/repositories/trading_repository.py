"""Repositories used to persist and query core trading records from the database."""

import logging

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.db.models import Position, StrategyRun, TradeOrder
from app.domain.trading import PositionRecord, StrategyRunRecord, TradeOrderRecord

logger = logging.getLogger(__name__)


class StrategyRunRepository:
    """Persist strategy evaluation outputs for analytics, replay, and auditability."""

    def __init__(self, session: Session) -> None:
        """Store the SQLAlchemy session used for writing and querying strategy-run records."""
        self.session = session

    def create_strategy_run(self, record: StrategyRunRecord) -> None:
        """Insert one strategy-run record and commit it immediately for traceability."""
        strategy_run = StrategyRun(
            symbol=record.symbol,
            timeframe=record.timeframe,
            short_window=record.short_window,
            long_window=record.long_window,
            action=record.action.value,
            confidence=record.confidence,
            reason=record.reason,
            metadata_json=record.metadata,
        )
        self.session.add(strategy_run)
        self.session.commit()
        logger.info("Strategy run saved", extra={"symbol": record.symbol, "action": record.action.value})

    def list_strategy_runs(self, symbol: str | None, limit: int, offset: int) -> tuple[int, list[StrategyRun]]:
        """Return paginated strategy-run history for operators and analytics workloads."""
        query = self.session.query(StrategyRun)
        if symbol:
            query = query.filter(StrategyRun.symbol == symbol)
        total = query.count()
        items = query.order_by(desc(StrategyRun.created_at)).offset(offset).limit(limit).all()
        return total, items


class TradeOrderRepository:
    """Persist generated orders so operations teams can inspect every submission attempt."""

    def __init__(self, session: Session) -> None:
        """Store the SQLAlchemy session used for writing and querying order records."""
        self.session = session

    def create_trade_order(self, record: TradeOrderRecord) -> None:
        """Insert one trade-order record and commit it immediately for durable order history."""
        trade_order = TradeOrder(
            symbol=record.symbol,
            action=record.action.value,
            quantity=record.quantity,
            status=record.status.value,
            requested_price=record.requested_price,
            broker_order_id=record.broker_order_id,
            dry_run=record.dry_run,
            metadata_json=record.metadata,
        )
        self.session.add(trade_order)
        self.session.commit()
        logger.info("Trade order saved", extra={"symbol": record.symbol, "status": record.status.value})

    def list_trade_orders(self, symbol: str | None, limit: int, offset: int) -> tuple[int, list[TradeOrder]]:
        """Return paginated order history so operators can review submission outcomes."""
        query = self.session.query(TradeOrder)
        if symbol:
            query = query.filter(TradeOrder.symbol == symbol)
        total = query.count()
        items = query.order_by(desc(TradeOrder.created_at)).offset(offset).limit(limit).all()
        return total, items


class PositionRepository:
    """Maintain the internal position snapshot that other services can later query and reconcile."""

    def __init__(self, session: Session) -> None:
        """Store the SQLAlchemy session used for upserting and querying positions."""
        self.session = session

    def upsert_position(self, record: PositionRecord) -> None:
        """Create or update a symbol position after execution so the platform has a durable exposure view."""
        position = self.session.query(Position).filter(Position.symbol == record.symbol).one_or_none()
        if position is None:
            position = Position(
                symbol=record.symbol,
                side=record.side.value,
                quantity=record.quantity,
                average_price=record.average_price,
                metadata_json=record.metadata,
            )
            self.session.add(position)
        else:
            position.side = record.side.value
            position.quantity = record.quantity
            position.average_price = record.average_price
            position.metadata_json = record.metadata

        self.session.commit()
        logger.info("Position upserted", extra={"symbol": record.symbol, "quantity": record.quantity, "side": record.side.value})

    def list_positions(self, symbol: str | None) -> tuple[int, list[Position]]:
        """Return the current internal position snapshot, optionally filtered to one symbol."""
        query = self.session.query(Position)
        if symbol:
            query = query.filter(Position.symbol == symbol)
        items = query.order_by(Position.symbol.asc()).all()
        return len(items), items
