from core.config import app_config
from db.base import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(app_config.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency for FastAPI routes and Celery tasks to get a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_db_and_tables():
    """
    Creates all database tables defined in models.py.
    This is useful for local development and initial setup when NOT using Alembic.
    For production, always rely on Alembic migrations.
    """
    Base.metadata.create_all(engine)
