"""Base processor for handling queue tasks."""

from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Generic, TypeVar

from edu_core.db.session import get_session_factory

T = TypeVar("T")


class BaseProcessor(ABC, Generic[T]):
    """Abstract base class for processing queue tasks.

    Each processor handles a specific task type with a typed payload.
    """

    @contextmanager
    def _get_db_session(self):
        """Context manager for database sessions with transaction handling.

        Yields:
            Database session

        Raises:
            Exception: If transaction fails, automatically rolls back
        """
        SessionLocal = get_session_factory()
        db = SessionLocal()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    @abstractmethod
    async def process(self, payload: T) -> None:
        """Process the task payload.

        Args:
            payload: The typed payload for this processor

        Raises:
            Exception: If processing fails
        """
        pass
