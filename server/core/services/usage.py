from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Literal

from sqlalchemy.orm import Session

from core.config import app_config
from core.exceptions import UsageLimitExceeded
from core.logger import get_logger
from db.models import UserUsage
from db.session import SessionLocal

logger = get_logger(__name__)


class UsageService:
    """Service for tracking and enforcing user usage limits."""

    def _get_or_create_usage(self, db: Session, user_id: str) -> UserUsage:
        """Get or create usage record for a user."""
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
            return usage
        except Exception as e:
            logger.error("error getting or creating usage: %s", e)
            raise

    def _reset_daily_counters_if_needed(self, db: Session, usage: UserUsage) -> UserUsage:
        """Reset daily counters if it's a new day."""
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
                    "reset daily counters for user_id=%s, date=%s",
                    usage.user_id,
                    now.date(),
                )
            except Exception as e:
                logger.error("error resetting daily counters: %s", e)
                raise

        return usage

    def check_and_increment(
        self,
        user_id: str,
        usage_type: Literal[
            "chat_message", "flashcard_generation", "quiz_generation", "document_upload"
        ],
    ) -> None:
        """
        Check if user has exceeded limit and increment counter.
        Raises UsageLimitExceeded if limit is exceeded.
        """
        with self._get_db_session() as db:
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
                    "usage limit exceeded user_id=%s, type=%s, count=%d, limit=%d",
                    user_id,
                    usage_type,
                    current_count,
                    limit,
                )
                raise UsageLimitExceeded(
                    usage_type=usage_type,
                    current_count=current_count,
                    limit=limit,
                )

            # Increment counter
            try:
                if usage_type == "chat_message":
                    usage.chat_messages_today += 1
                elif usage_type == "flashcard_generation":
                    usage.flashcard_generations_today += 1
                elif usage_type == "quiz_generation":
                    usage.quiz_generations_today += 1
                elif usage_type == "document_upload":
                    usage.document_uploads_today += 1

                db.commit()
                db.refresh(usage)
                
                # Get new count for logging
                if usage_type == "chat_message":
                    new_count = usage.chat_messages_today
                elif usage_type == "flashcard_generation":
                    new_count = usage.flashcard_generations_today
                elif usage_type == "quiz_generation":
                    new_count = usage.quiz_generations_today
                elif usage_type == "document_upload":
                    new_count = usage.document_uploads_today
                else:
                    new_count = 0
                    
                logger.info(
                    "incremented usage user_id=%s, type=%s, new_count=%d",
                    user_id,
                    usage_type,
                    new_count,
                )
            except Exception as e:
                logger.error("error incrementing usage: %s", e)
                raise

    def get_usage(self, user_id: str) -> dict:
        """Get current usage statistics for a user."""
        with self._get_db_session() as db:
            usage = self._get_or_create_usage(db, user_id)
            usage = self._reset_daily_counters_if_needed(db, usage)

            return {
                "chat_messages": {
                    "used": usage.chat_messages_today,
                    "limit": app_config.MAX_CHAT_MESSAGES_PER_DAY,
                },
                "flashcard_generations": {
                    "used": usage.flashcard_generations_today,
                    "limit": app_config.MAX_FLASHCARD_GENERATIONS_PER_DAY,
                },
                "quiz_generations": {
                    "used": usage.quiz_generations_today,
                    "limit": app_config.MAX_QUIZ_GENERATIONS_PER_DAY,
                },
                "document_uploads": {
                    "used": usage.document_uploads_today,
                    "limit": app_config.MAX_DOCUMENT_UPLOADS_PER_DAY,
                },
            }

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

