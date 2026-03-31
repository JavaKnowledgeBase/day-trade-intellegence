"""Health and readiness endpoints for platform monitoring."""

from fastapi import APIRouter, Depends, status

from app.core.dependencies import get_operational_status_service
from app.core.settings import get_settings
from app.services.operational_service import OperationalStatusService

router = APIRouter()


@router.get("/")
async def service_root() -> dict[str, str]:
    """Return a small landing payload that helps local users discover the template's entry points."""
    settings = get_settings()
    return {
        "name": settings.app_name,
        "environment": settings.environment,
        "docs": "/docs",
        "api_prefix": settings.api_prefix,
    }


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Return a lightweight liveness response for load balancers and monitoring systems."""
    settings = get_settings()
    return {"status": "ok", "environment": settings.environment}


@router.get("/ready", status_code=status.HTTP_200_OK)
def readiness_check(
    operational_status_service: OperationalStatusService = Depends(get_operational_status_service),
) -> dict:
    """Return dependency readiness information so operators can distinguish live from truly ready."""
    return operational_status_service.get_system_status()
