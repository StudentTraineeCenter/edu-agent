"""Service for tracking and enforcing user usage limits."""

from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Literal

from sqlalchemy.orm import Session

from core.config import app_config
from core.exceptions import UsageLimitExceeded
from core.logger import get_logger
from db.models import UserUsage
from db.session import SessionLocal
from schemas.usage import UsageLimit, UsageStats

logger = get_logger(__name__)


class UsageService:
    """Service for tracking and enforcing user usage limits."""

    def __init__(self) -> None:
        """Initialize the usage service."""
        pass

    def check_and_increment(
        self,
        user_id: str,
        usage_type: Literal[
            "chat_message", "flashcard_generation", "quiz_generation", "document_upload"
        ],
    ) -> None:
        """Check if user has exceeded limit and increment counter.

        Args:
            user_id: The user's unique identifier
            usage_type: Type of usage to check and increment

        Raises:
            UsageLimitExceeded: If the user has exceeded their usage limit
        """
        with self._get_db_session() as db:
            try:
                usage = self._get_or_create_usage(db, user_id)
                usage = self._reset_daily_counters_if_needed(db, usage)

                # Get current count and limit
                count_map = {
                    "chat_message": usage.chat_messages_today,
                    "flashcard_generation": usage.flashcard_generations_today,
                    "quiz_generation": usage.quiz_generations_today,
                    "document_upload": usage.document_uploads_today,
                }

                limit_map = {
                    "chat_message": app_config.MAX_CHAT_MESSAGES_PER_DAY,
                    "flashcard_generation": app_config.MAX_FLASHCARD_GENERATIONS_PER_DAY,
                    "quiz_generation": app_config.MAX_QUIZ_GENERATIONS_PER_DAY,
                    "document_upload": app_config.MAX_DOCUMENT_UPLOADS_PER_DAY,
                }

                current_count = count_map[usage_type]
                limit = limit_map[usage_type]

                # Check limit
                if current_count >= limit:
                    logger.warning(
                        f"usage limit exceeded user_id={user_id}, type={usage_type}, count={current_count}, limit={limit}"
                    )
                    raise UsageLimitExceeded(
                        usage_type=usage_type,
                        current_count=current_count,
                        limit=limit,
                    )

                # Increment counter
                if usage_type == "chat_message":
                    usage.chat_messages_today += 1
                    new_count = usage.chat_messages_today
                elif usage_type == "flashcard_generation":
                    usage.flashcard_generations_today += 1
                    new_count = usage.flashcard_generations_today
                elif usage_type == "quiz_generation":
                    usage.quiz_generations_today += 1
                    new_count = usage.quiz_generations_today
                elif usage_type == "document_upload":
                    usage.document_uploads_today += 1
                    new_count = usage.document_uploads_today
                else:
                    new_count = 0

                db.commit()
                db.refresh(usage)

                logger.info(
                    f"incremented usage user_id={user_id}, type={usage_type}, new_count={new_count}"
                )
            except UsageLimitExceeded:
                raise
            except Exception as e:
                logger.error_structured("error incrementing usage", user_id=user_id, error=str(e), exc_info=True)
                raise

    def get_usage(self, user_id: str) -> UsageStats:
        """Get current usage statistics for a user.

        Args:
            user_id: The user's unique identifier

        Returns:
            UsageStats containing usage statistics for all usage types
        """
        with self._get_db_session() as db:
            try:
                usage = self._get_or_create_usage(db, user_id)
                usage = self._reset_daily_counters_if_needed(db, usage)

                return UsageStats(
                    chat_messages=UsageLimit(
                        used=usage.chat_messages_today,
                        limit=app_config.MAX_CHAT_MESSAGES_PER_DAY,
                    ),
                    flashcard_generations=UsageLimit(
                        used=usage.flashcard_generations_today,
                        limit=app_config.MAX_FLASHCARD_GENERATIONS_PER_DAY,
                    ),
                    quiz_generations=UsageLimit(
                        used=usage.quiz_generations_today,
                        limit=app_config.MAX_QUIZ_GENERATIONS_PER_DAY,
                    ),
                    document_uploads=UsageLimit(
                        used=usage.document_uploads_today,
                        limit=app_config.MAX_DOCUMENT_UPLOADS_PER_DAY,
                    ),
                )
            except Exception as e:
                logger.error_structured("error getting usage", user_id=user_id, error=str(e), exc_info=True)
                raise

    def _get_or_create_usage(self, db: Session, user_id: str) -> UserUsage:
        """Get or create usage record for a user.

        Args:
            db: Database session
            user_id: The user's unique identifier

        Returns:
            UserUsage model instance
        """
        try:
            usage = db.query(UserUsage).filter(UserUsage.user_id == user_id).first()
            if not usage:
                usage = UserUsage(
                    user_id=user_id,
                    chat_messages_today=0,
                    flashcard_generations_today=0,
                    quiz_generations_today=0,
                    document_uploads_today=0,
                    last_reset_date=datetime.now(timezone.utc),
                )
                db.add(usage)
                db.commit()
                db.refresh(usage)
                logger.info_structured("created usage record", user_id=user_id)
            return usage
        except Exception as e:
            logger.error_structured("error getting or creating usage", user_id=user_id, error=str(e), exc_info=True)
            raise

    def _reset_daily_counters_if_needed(
        self, db: Session, usage: UserUsage
    ) -> UserUsage:
        """Reset daily counters if it's a new day.

        Args:
            db: Database session
            usage: UserUsage model instance

        Returns:
            Updated UserUsage model instance
        """
        now = datetime.now(timezone.utc)
        last_reset = usage.last_reset_date

        # Check if it's a new day (compare dates, not times)
        if now.date() > last_reset.date():
            try:
                usage.chat_messages_today = 0
                usage.flashcard_generations_today = 0
                usage.quiz_generations_today = 0
                usage.document_uploads_today = 0
                usage.last_reset_date = now
                db.commit()
                db.refresh(usage)
                logger.info(
                    f"reset daily counters for user_id={usage.user_id}, date={now.date()}"
                )
            except Exception as e:
                logger.error(
                    f"error resetting daily counters for user_id={usage.user_id}: {e}"
                )
                raise

        return usage

    @contextmanager
    def _get_db_session(self):
        """Context manager for database sessions."""
        db = SessionLocal()
        try:
            yield db
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
