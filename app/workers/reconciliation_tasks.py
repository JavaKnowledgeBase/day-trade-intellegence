"""Background tasks that reconcile persisted positions against broker account state."""

import asyncio
import logging

from app.core.dependencies import get_reconciliation_service
from app.db.session import SessionLocal
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="reconcile_positions")
def reconcile_positions_task(use_live_data: bool = True) -> dict:
    """Run the reconciliation workflow in a worker process and return a summarized task result."""
    session = SessionLocal()
    try:
        service = get_reconciliation_service(session)
        response = asyncio.run(service.reconcile_positions(use_live_data=use_live_data))
        return response.model_dump(mode="json")
    except Exception as exc:
        logger.exception("Broker reconciliation background task failed")
        raise exc
    finally:
        session.close()
