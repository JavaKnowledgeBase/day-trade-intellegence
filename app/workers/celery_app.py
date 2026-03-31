"""Celery application bootstrap for scheduled and asynchronous jobs."""

from celery import Celery

from app.core.settings import get_settings

settings = get_settings()

# This worker bootstrap creates the shared Celery app used for background jobs,
# scheduled market scans, and broker reconciliation tasks.
celery_app = Celery("day_trade_intelligence", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "scheduled-position-reconciliation": {
            "task": "reconcile_positions",
            "schedule": 300.0,
            "args": (False,),
        }
    },
)

# Import task modules after the Celery app exists so tasks register themselves
# against the shared worker instance without bootstrap-order issues.
import app.workers.reconciliation_tasks  # noqa: E402,F401
