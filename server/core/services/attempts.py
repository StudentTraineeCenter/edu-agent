from contextlib import contextmanager
from typing import List

from core.logger import get_logger
from db.models import Flashcard, QuizQuestion, StudyAttempt
from db.session import SessionLocal

logger = get_logger(__name__)


class AttemptService:
    """Service for managing study attempts."""

    def __init__(self):
        """Initialize the attempt service."""

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

    def _validate_item(self, db, item_type: str, item_id: str) -> bool:
        """Validate that the referenced item exists."""
        try:
            if item_type == "flashcard":
                flashcard = db.query(Flashcard).filter(Flashcard.id == item_id).first()
                return flashcard is not None
            elif item_type == "quiz":
                question = (
                    db.query(QuizQuestion).filter(QuizQuestion.id == item_id).first()
                )
                return question is not None
            else:
                return False
        except Exception as e:
            logger.error("error validating item: %s", e)
            return False

    def create_attempt(
        self,
        user_id: str,
        project_id: str,
        item_type: str,
        item_id: str,
        topic: str,
        user_answer: str | None,
        correct_answer: str,
        was_correct: bool,
    ) -> StudyAttempt:
        """Create a single attempt record."""
        with self._get_db_session() as db:
            try:
                # Validate that the referenced item exists
                if not self._validate_item(db, item_type, item_id):
                    raise ValueError(
                        f"Item {item_id} of type {item_type} not found"
                    )

                attempt = StudyAttempt(
                    user_id=user_id,
                    project_id=project_id,
                    item_type=item_type,
                    item_id=item_id,
                    topic=topic,
                    user_answer=user_answer,
                    correct_answer=correct_answer,
                    was_correct=was_correct,
                )

                db.add(attempt)
                db.commit()
                db.refresh(attempt)

                logger.info(
                    "created attempt id=%s for user_id=%s, item_type=%s, item_id=%s",
                    attempt.id,
                    user_id,
                    item_type,
                    item_id,
                )

                return attempt

            except Exception as e:
                logger.error("error creating attempt: %s", e)
                db.rollback()
                raise

    def create_attempts_batch(
        self,
        user_id: str,
        project_id: str,
        attempts_data: List[dict],
    ) -> List[StudyAttempt]:
        """Create multiple attempt records in a batch."""
        with self._get_db_session() as db:
            try:
                created_attempts = []

                for attempt_data in attempts_data:
                    # Validate that the referenced item exists
                    item_type = attempt_data.get("item_type")
                    item_id = attempt_data.get("item_id")

                    if not self._validate_item(db, item_type, item_id):
                        logger.warning(
                            "skipping attempt: item %s of type %s not found",
                            item_id,
                            item_type,
                        )
                        continue

                    attempt = StudyAttempt(
                        user_id=user_id,
                        project_id=project_id,
                        item_type=item_type,
                        item_id=item_id,
                        topic=attempt_data.get("topic"),
                        user_answer=attempt_data.get("user_answer"),
                        correct_answer=attempt_data.get("correct_answer"),
                        was_correct=attempt_data.get("was_correct"),
                    )

                    db.add(attempt)
                    created_attempts.append(attempt)

                db.commit()

                # Refresh all attempts
                for attempt in created_attempts:
                    db.refresh(attempt)

                logger.info(
                    "created %d attempts for user_id=%s, project_id=%s",
                    len(created_attempts),
                    user_id,
                    project_id,
                )

                return created_attempts

            except Exception as e:
                logger.error("error creating attempts batch: %s", e)
                db.rollback()
                raise

    def get_user_attempts(
        self, user_id: str, project_id: str | None = None
    ) -> List[StudyAttempt]:
        """Retrieve attempts for a user, optionally filtered by project."""
        with self._get_db_session() as db:
            try:
                query = db.query(StudyAttempt).filter(StudyAttempt.user_id == user_id)

                if project_id:
                    query = query.filter(StudyAttempt.project_id == project_id)

                attempts = query.order_by(StudyAttempt.created_at.desc()).all()

                logger.info(
                    "retrieved %d attempts for user_id=%s, project_id=%s",
                    len(attempts),
                    user_id,
                    project_id,
                )

                return attempts

            except Exception as e:
                logger.error("error retrieving attempts: %s", e)
                raise

