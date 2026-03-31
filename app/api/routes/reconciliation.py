"""Endpoints used to trigger and inspect broker reconciliation workflows."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db_session, get_query_service, get_reconciliation_service
from app.domain.reconciliation import ReconciliationResponse, ReconciliationRunListResponse
from app.security.auth import UserRole, require_role
from app.services.query_service import TradingQueryService
from app.services.reconciliation_service import ReconciliationService

router = APIRouter()


@router.post("/run", response_model=ReconciliationResponse, status_code=status.HTTP_200_OK)
async def run_reconciliation(
    session: Annotated[Session, Depends(get_db_session)],
    _: Annotated[UserRole, Depends(require_role({UserRole.OPERATOR, UserRole.ADMIN}))],
    live: bool = Query(default=True),
) -> ReconciliationResponse:
    """Run reconciliation synchronously so an operator can inspect mismatches immediately."""
    service: ReconciliationService = get_reconciliation_service(session)
    return await service.reconcile_positions(use_live_data=live)


@router.post("/run/background", status_code=status.HTTP_202_ACCEPTED)
def enqueue_reconciliation(
    _: Annotated[UserRole, Depends(require_role({UserRole.OPERATOR, UserRole.ADMIN}))],
    live: bool = Query(default=True),
) -> dict[str, str | bool]:
    """Enqueue a reconciliation task so broker-sync checks can run asynchronously in Celery."""
    from app.workers.reconciliation_tasks import reconcile_positions_task

    task = reconcile_positions_task.delay(use_live_data=live)
    return {"task_id": task.id, "queued": True}


@router.get("/runs", response_model=ReconciliationRunListResponse, status_code=status.HTTP_200_OK)
def list_reconciliation_runs(
    session: Annotated[Session, Depends(get_db_session)],
    _: Annotated[UserRole, Depends(require_role({UserRole.OPERATOR, UserRole.ADMIN}))],
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> ReconciliationRunListResponse:
    """Return paginated reconciliation history so operators can inspect broker-sync outcomes over time."""
    query_service: TradingQueryService = get_query_service(session)
    return query_service.list_reconciliation_runs(limit=limit, offset=offset)
