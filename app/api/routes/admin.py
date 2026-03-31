"""Admin endpoints that expose system-level operational visibility."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.dependencies import get_operational_status_service
from app.security.auth import UserRole, require_role
from app.services.operational_service import OperationalStatusService

router = APIRouter()


@router.get("/system/status", status_code=status.HTTP_200_OK)
def get_system_status(
    _: Annotated[UserRole, Depends(require_role({UserRole.ADMIN}))],
    operational_status_service: OperationalStatusService = Depends(get_operational_status_service),
) -> dict:
    """Return an admin-only snapshot of application, database, Redis, and bootstrap status."""
    return operational_status_service.get_system_status()
