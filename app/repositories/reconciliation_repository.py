"""Repository used to persist and query broker reconciliation history."""

import logging

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.db.models import ReconciliationRun
from app.domain.reconciliation import ReconciliationRunRecord

logger = logging.getLogger(__name__)


class ReconciliationRepository:
    """Persist reconciliation outcomes so operations teams can review sync health over time."""

    def __init__(self, session: Session) -> None:
        """Store the SQLAlchemy session used for inserts and reconciliation history queries."""
        self.session = session

    def create_reconciliation_run(self, record: ReconciliationRunRecord) -> None:
        """Insert one reconciliation run and commit it immediately for durable operational history."""
        run = ReconciliationRun(
            status=record.status.value,
            source=record.source,
            checked_symbols=record.checked_symbols,
            mismatched_symbols=record.mismatched_symbols,
            detail=record.detail,
            metadata_json=record.metadata,
        )
        self.session.add(run)
        self.session.commit()
        logger.info("Reconciliation run saved", extra={"status": record.status.value, "mismatched_symbols": record.mismatched_symbols})

    def list_reconciliation_runs(self, limit: int, offset: int) -> tuple[int, list[ReconciliationRun]]:
        """Return paginated reconciliation history for operator-facing read APIs."""
        query = self.session.query(ReconciliationRun)
        total = query.count()
        items = query.order_by(desc(ReconciliationRun.created_at)).offset(offset).limit(limit).all()
        return total, items
