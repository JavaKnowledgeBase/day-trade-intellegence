"""Database engine and session management for the trading platform."""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.settings import get_settings

# The shared declarative base is used by repository models so the application
# can later evolve into a full persistence layer with migrations.
Base = declarative_base()


def _build_engine():
    """Create the SQLAlchemy engine lazily so imports do not fail before settings are resolved."""
    settings = get_settings()
    connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
    return create_engine(settings.database_url, pool_pre_ping=True, connect_args=connect_args)


engine = _build_engine()

# SessionLocal is the factory used by repositories whenever they need a short-
# lived database session for audit logging or future transactional workflows.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
