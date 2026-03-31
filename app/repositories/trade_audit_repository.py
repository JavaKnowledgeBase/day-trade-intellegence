"""Repository used to persist and query trade audit events from the database."""

import logging

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.db.models import TradeAuditLog
from app.domain.trading import TradeAuditRecord

logger = logging.getLogger(__name__)


class TradeAuditRepository:
    """Persist structured trade lifecycle events without leaking ORM details into services."""

    def __init__(self, session: Session) -> None:
        """Store the active SQLAlchemy session used for inserts and queries."""
        self.session = session

    def create_audit_log(self, record: TradeAuditRecord) -> None:
        """Insert one trade audit record and commit it immediately for operational traceability."""
        audit_log = TradeAuditLog(
            symbol=record.symbol,
            status=record.status.value,
            detail=record.detail,
            metadata_json=record.metadata,
        )
        self.session.add(audit_log)
        self.session.commit()
        logger.info("Trade audit log saved", extra={"symbol": record.symbol, "status": record.status.value})

    def list_audit_logs(self, symbol: str | None, limit: int, offset: int) -> tuple[int, list[TradeAuditLog]]:
        """Return paginated audit logs so operators can inspect the trade lifecycle history."""
        query = self.session.query(TradeAuditLog)
        if symbol:
            query = query.filter(TradeAuditLog.symbol == symbol)
        total = query.count()
        items = query.order_by(desc(TradeAuditLog.created_at)).offset(offset).limit(limit).all()
        return total, items
