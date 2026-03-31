"""Service that reconciles internal persisted positions against broker-reported portfolio state."""

import logging

from app.domain.portfolio import PortfolioSnapshot
from app.domain.reconciliation import PositionReconciliationItem, ReconciliationResponse, ReconciliationRunRecord, ReconciliationStatus
from app.domain.trading import PositionRead
from app.repositories.reconciliation_repository import ReconciliationRepository
from app.services.portfolio_service import PortfolioService
from app.services.query_service import TradingQueryService

logger = logging.getLogger(__name__)


class ReconciliationService:
    """Compare internal positions with broker data, persist the outcome, and return a normalized summary."""

    def __init__(self, portfolio_service: PortfolioService, query_service: TradingQueryService, reconciliation_repository: ReconciliationRepository) -> None:
        """Store the service dependencies required to fetch state, compare it, and persist results."""
        self.portfolio_service = portfolio_service
        self.query_service = query_service
        self.reconciliation_repository = reconciliation_repository

    async def reconcile_positions(self, use_live_data: bool = True) -> ReconciliationResponse:
        """Fetch broker and internal positions, compare them symbol by symbol, and save the reconciliation result."""
        try:
            portfolio_snapshot = await self.portfolio_service.get_portfolio_snapshot(use_live_data=use_live_data)
            internal_positions = self.query_service.list_positions(symbol=None)
            items = self._compare_positions(internal_positions.items, portfolio_snapshot)
            mismatched_symbols = sum(1 for item in items if not item.matched)
            status = ReconciliationStatus.MATCHED if mismatched_symbols == 0 else ReconciliationStatus.MISMATCHED
            detail = "All positions matched broker state." if mismatched_symbols == 0 else "Position mismatches detected during reconciliation."
            response = ReconciliationResponse(status=status, source=portfolio_snapshot.source, checked_symbols=len(items), mismatched_symbols=mismatched_symbols, items=items, detail=detail)
            self.reconciliation_repository.create_reconciliation_run(ReconciliationRunRecord(status=status, source=portfolio_snapshot.source, checked_symbols=len(items), mismatched_symbols=mismatched_symbols, detail=detail, metadata={"items": [item.model_dump() for item in items]}))
            logger.info("Position reconciliation completed", extra={"status": status.value, "checked_symbols": len(items), "mismatched_symbols": mismatched_symbols})
            return response
        except Exception as exc:
            logger.exception("Position reconciliation failed")
            self.reconciliation_repository.create_reconciliation_run(ReconciliationRunRecord(status=ReconciliationStatus.FAILED, source="ibkr" if use_live_data else "paper", checked_symbols=0, mismatched_symbols=0, detail="Reconciliation failed.", metadata={"error_type": exc.__class__.__name__, "message": str(exc)}))
            raise

    def _compare_positions(self, internal_positions: list[PositionRead], portfolio_snapshot: PortfolioSnapshot) -> list[PositionReconciliationItem]:
        """Build a symbol-by-symbol comparison between persisted positions and broker positions."""
        broker_by_symbol = {position.symbol: position for position in portfolio_snapshot.positions}
        internal_by_symbol = {position.symbol: position for position in internal_positions}
        all_symbols = sorted(set(broker_by_symbol) | set(internal_by_symbol))
        items = []

        for symbol in all_symbols:
            internal = internal_by_symbol.get(symbol)
            broker = broker_by_symbol.get(symbol)
            internal_quantity = float(internal.quantity) if internal else 0.0
            broker_quantity = float(broker.quantity) if broker else 0.0
            internal_average_price = float(internal.average_price) if internal else 0.0
            broker_average_price = float(broker.average_cost) if broker else 0.0
            quantity_difference = internal_quantity - broker_quantity
            price_difference = internal_average_price - broker_average_price
            matched = abs(quantity_difference) < 0.0001 and abs(price_difference) < 0.01
            items.append(PositionReconciliationItem(symbol=symbol, internal_quantity=internal_quantity, broker_quantity=broker_quantity, quantity_difference=quantity_difference, internal_average_price=internal_average_price, broker_average_price=broker_average_price, price_difference=price_difference, matched=matched))

        return items
