"""Container bootstrap helper that waits for backing services and optionally runs migrations."""

import os
import socket
import subprocess
import sys
import time
from urllib.parse import urlparse


def wait_for_tcp_service(host: str, port: int, name: str, timeout_seconds: int = 60) -> None:
    """Wait until a TCP service accepts connections so containers start in a predictable order."""
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=2):
                print(f"{name} is reachable at {host}:{port}")
                return
        except OSError:
            time.sleep(2)
    raise TimeoutError(f"Timed out waiting for {name} at {host}:{port}")


def maybe_wait_for_database() -> None:
    """Wait for the configured database when it uses a networked URL rather than local SQLite."""
    database_url = os.getenv("DATABASE_URL", "sqlite:///./day_trade_intelligence.db")
    if database_url.startswith("sqlite"):
        print("SQLite detected; database wait skipped")
        return
    parsed = urlparse(database_url)
    wait_for_tcp_service(parsed.hostname or "db", parsed.port or 5432, "database")


def maybe_wait_for_redis() -> None:
    """Wait for Redis when a Redis URL is configured for worker and readiness paths."""
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    parsed = urlparse(redis_url)
    wait_for_tcp_service(parsed.hostname or "redis", parsed.port or 6379, "redis")


def maybe_run_migrations() -> None:
    """Run Alembic migrations inside the container when explicitly enabled."""
    if os.getenv("RUN_MIGRATIONS_ON_START", "false").lower() != "true":
        print("Startup migrations disabled; skipping")
        return
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True)
    print("Alembic migrations completed")


if __name__ == "__main__":
    maybe_wait_for_database()
    maybe_wait_for_redis()
    maybe_run_migrations()
