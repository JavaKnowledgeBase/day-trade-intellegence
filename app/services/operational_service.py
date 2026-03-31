"""Operational status checks used by readiness and admin system endpoints."""

import logging

from sqlalchemy import text

from app.core.settings import Settings
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)

try:
    import redis
except Exception:
    redis = None


class OperationalStatusService:
    """Provide lightweight infrastructure checks so operators can verify system readiness."""

    def __init__(self, settings: Settings) -> None:
        """Store settings needed to reach backing services such as the database and Redis."""
        self.settings = settings

    def get_system_status(self) -> dict:
        """Return a summary of app, database, and Redis status for operator visibility."""
        db_status = self._check_database()
        redis_status = self._check_redis()
        ready = db_status["ok"] and redis_status["ok"]
        return {
            "app": {"ok": True, "environment": self.settings.environment, "name": self.settings.app_name},
            "database": db_status,
            "redis": redis_status,
            "ready": ready,
            "bootstrap": {
                "bootstrap_schema": self.settings.bootstrap_schema,
                "run_migrations_on_start": self.settings.run_migrations_on_start,
                "seed_demo_data": self.settings.seed_demo_data,
            },
        }

    def _check_database(self) -> dict:
        """Run a minimal SQL query to verify the database engine is reachable."""
        session = SessionLocal()
        try:
            session.execute(text("SELECT 1"))
            return {"ok": True, "url": self.settings.database_url}
        except Exception as exc:
            logger.exception("Database readiness check failed")
            return {"ok": False, "url": self.settings.database_url, "detail": str(exc)}
        finally:
            session.close()

    def _check_redis(self) -> dict:
        """Ping Redis with a short timeout so readiness checks stay responsive when Redis is unavailable."""
        if redis is None:
            return {"ok": False, "url": self.settings.redis_url, "detail": "redis package unavailable"}
        try:
            client = redis.Redis.from_url(self.settings.redis_url, socket_connect_timeout=0.5, socket_timeout=0.5)
            client.ping()
            return {"ok": True, "url": self.settings.redis_url}
        except Exception as exc:
            logger.exception("Redis readiness check failed")
            return {"ok": False, "url": self.settings.redis_url, "detail": str(exc)}
