"""Service for tracking and enforcing user usage limits."""

from contextlib import contextmanager
from datetime import UTC, datetime
from typing import Literal

from sqlalchemy.orm import Session

from edu_core.db.models import UserUsage
from edu_core.db.session import get_session_factory
from edu_core.exceptions import UsageLimitExceededError
from edu_core.schemas.usage import UsageDto, UsageLimitDto


class UsageService:
    """Service for tracking and enforcing user usage limits."""

    def __init__(
        self,
        max_chat_messages_per_day: int = 50,
        max_flashcard_generations_per_day: int = 10,
        max_quiz_generations_per_day: int = 10,
        max_mindmap_generations_per_day: int = 10,
        max_document_uploads_per_day: int = 5,
    ) -> None:
        """Initialize the usage service.

        Args:
            max_chat_messages_per_day: Maximum chat messages per day
            max_flashcard_generations_per_day: Maximum flashcard generations per day
            max_quiz_generations_per_day: Maximum quiz generations per day
            max_mindmap_generations_per_day: Maximum mind map generations per day
            max_document_uploads_per_day: Maximum document uploads per day
        """
        self.max_chat_messages_per_day = max_chat_messages_per_day
        self.max_flashcard_generations_per_day = max_flashcard_generations_per_day
        self.max_quiz_generations_per_day = max_quiz_generations_per_day
        self.max_mindmap_generations_per_day = max_mindmap_generations_per_day
        self.max_document_uploads_per_day = max_document_uploads_per_day

    def check_and_increment(
        self,
        user_id: str,
        usage_type: Literal[
            "chat_message",
            "flashcard_generation",
            "quiz_generation",
            "mindmap_generation",
            "document_upload",
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
                    "mindmap_generation": usage.mindmap_generations_today,
                    "document_upload": usage.document_uploads_today,
                }

                limit_map = {
                    "chat_message": self.max_chat_messages_per_day,
                    "flashcard_generation": self.max_flashcard_generations_per_day,
                    "quiz_generation": self.max_quiz_generations_per_day,
                    "mindmap_generation": self.max_mindmap_generations_per_day,
                    "document_upload": self.max_document_uploads_per_day,
                }

                current_count = count_map[usage_type]
                limit = limit_map[usage_type]

                # Check limit
                if current_count >= limit:
                    raise UsageLimitExceededError(
                        usage_type=usage_type,
                        current_count=current_count,
                        limit=limit,
                    )

                # Increment counter
                if usage_type == "chat_message":
                    usage.chat_messages_today += 1
                elif usage_type == "flashcard_generation":
                    usage.flashcard_generations_today += 1
                elif usage_type == "quiz_generation":
                    usage.quiz_generations_today += 1
                elif usage_type == "mindmap_generation":
                    usage.mindmap_generations_today += 1
                elif usage_type == "document_upload":
                    usage.document_uploads_today += 1

                db.commit()
                db.refresh(usage)
            except UsageLimitExceededError:
                raise
            except Exception:
                db.rollback()
                raise

    def get_usage(self, user_id: str) -> UsageDto:
        """Get current usage statistics for a user.

        Args:
            user_id: The user's unique identifier

        Returns:
            UsageDto containing usage statistics for all usage types
        """
        with self._get_db_session() as db:
            try:
                usage = self._get_or_create_usage(db, user_id)
                usage = self._reset_daily_counters_if_needed(db, usage)

                return UsageDto(
                    chat_messages=UsageLimitDto(
                        used=usage.chat_messages_today,
                        limit=self.max_chat_messages_per_day,
                    ),
                    flashcard_generations=UsageLimitDto(
                        used=usage.flashcard_generations_today,
                        limit=self.max_flashcard_generations_per_day,
                    ),
                    quiz_generations=UsageLimitDto(
                        used=usage.quiz_generations_today,
                        limit=self.max_quiz_generations_per_day,
                    ),
                    mindmap_generations=UsageLimitDto(
                        used=usage.mindmap_generations_today,
                        limit=self.max_mindmap_generations_per_day,
                    ),
                    document_uploads=UsageLimitDto(
                        used=usage.document_uploads_today,
                        limit=self.max_document_uploads_per_day,
                    ),
                )
            except Exception:
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
                    mindmap_generations_today=0,
                    document_uploads_today=0,
                    last_reset_date=datetime.now(UTC),
                )
                db.add(usage)
                db.commit()
                db.refresh(usage)
            return usage
        except Exception:
            db.rollback()
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
        now = datetime.now(UTC)
        last_reset = usage.last_reset_date

        # Check if it's a new day (compare dates, not times)
        if now.date() > last_reset.date():
            try:
                usage.chat_messages_today = 0
                usage.flashcard_generations_today = 0
                usage.quiz_generations_today = 0
                usage.mindmap_generations_today = 0
                usage.document_uploads_today = 0
                usage.last_reset_date = now
                db.commit()
                db.refresh(usage)
            except Exception:
                db.rollback()
                raise

        return usage

    @contextmanager
    def _get_db_session(self):
        """Context manager for database sessions."""
        SessionLocal = get_session_factory()
        db = SessionLocal()
        try:
            yield db
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
