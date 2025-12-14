from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from edu_shared.db.base import Base

# 1. Global Placeholders (Initially None)
_engine = None
_SessionLocal = None


def init_db(database_url: str) -> None:
    """
    Initialize the global database engine and session factory.
    Call this ONCE at the start of your application (API lifespan or Worker startup).
    """
    global _engine, _SessionLocal

    if _engine is not None:
        return  # Already initialized, skip

    # Create the engine
    _engine = create_engine(database_url, pool_pre_ping=True)

    # Create the session factory
    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


def get_db() -> Generator[Session]:
    """
    FastAPI dependency. Yields a database session.
    Fails nicely if you forgot to call init_db().
    """
    if _SessionLocal is None:
        raise RuntimeError(
            "Database not initialized. You must call 'init_db(url)' on startup."
        )

    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_db_and_tables() -> None:
    """
    Creates tables. Useful for dev/testing.
    """
    if _engine is None:
        raise RuntimeError("Database not initialized.")

    # Import models so Base.metadata finds them
    from edu_shared.db import models  # noqa: F401

    Base.metadata.create_all(_engine)


# Helper for manual session usage (e.g. in Worker scripts)
def get_session_factory():
    if _SessionLocal is None:
        raise RuntimeError("Database not initialized.")
    return _SessionLocal
