"""Service for managing study attempts."""

from contextlib import contextmanager
from typing import List

from sqlalchemy.orm import Session

from core.logger import get_logger
from db.models import Flashcard, QuizQuestion, StudyAttempt
from db.session import SessionLocal

logger = get_logger(__name__)


class AttemptService:
    """Service for managing study attempts."""

    def __init__(self) -> None:
        """Initialize the attempt service."""
        pass

    def create_attempt(
        self,
        user_id: str,
        project_id: str,
        study_resource_type: str,
        study_resource_id: str,
        topic: str,
        user_answer: str | None,
        correct_answer: str,
        was_correct: bool,
    ) -> StudyAttempt:
        """Create a single attempt record.

        Args:
            user_id: The user's unique identifier
            project_id: The project ID
            study_resource_type: Type of study resource ('flashcard' or 'quiz')
            study_resource_id: ID of the flashcard or quiz question
            topic: Topic of the study resource
            user_answer: User's answer (can be None for flashcards)
            correct_answer: The correct answer
            was_correct: Whether the user's answer was correct

        Returns:
            Created StudyAttempt model instance

        Raises:
            ValueError: If the referenced study resource doesn't exist
        """
        with self._get_db_session() as db:
            try:
                # Validate that the referenced study resource exists
                if not self._validate_item(db, study_resource_type, study_resource_id):
                    raise ValueError(f"Study resource {study_resource_id} of type {study_resource_type} not found")

                attempt = StudyAttempt(
                    user_id=user_id,
                    project_id=project_id,
                    item_type=study_resource_type,
                    item_id=study_resource_id,
                    topic=topic,
                    user_answer=user_answer,
                    correct_answer=correct_answer,
                    was_correct=was_correct,
                )

                db.add(attempt)
                db.commit()
                db.refresh(attempt)

                logger.info(
                    f"created attempt id={attempt.id} for user_id={user_id}, item_type={study_resource_type}, item_id={study_resource_id}"
                )

                return attempt
            except ValueError:
                raise
            except Exception as e:
                logger.error(
                    f"error creating attempt for user_id={user_id}, item_id={study_resource_id}: {e}"
                )
                raise

    def create_attempts_batch(
        self,
        user_id: str,
        project_id: str,
        attempts_data: List[dict],
    ) -> List[StudyAttempt]:
        """Create multiple attempt records in a batch.

        Args:
            user_id: The user's unique identifier
            project_id: The project ID
            attempts_data: List of dictionaries containing attempt data

        Returns:
            List of created StudyAttempt model instances
        """
        with self._get_db_session() as db:
            try:
                created_attempts = []

                for attempt_data in attempts_data:
                    item_type = attempt_data.get("item_type")
                    item_id = attempt_data.get("item_id")

                    # Validate that the referenced study resource exists
                    if not self._validate_item(db, item_type, item_id):
                        logger.warning(
                            f"skipping attempt: study resource {item_id} of type {item_type} not found"
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
                    f"created {len(created_attempts)} attempts for user_id={user_id}, project_id={project_id}"
                )

                return created_attempts
            except Exception as e:
                logger.error(
                    f"error creating attempts batch for user_id={user_id}, project_id={project_id}: {e}"
                )
                raise

    def get_user_attempts(
        self, user_id: str, project_id: str | None = None
    ) -> List[StudyAttempt]:
        """Retrieve attempts for a user, optionally filtered by project.

        Args:
            user_id: The user's unique identifier
            project_id: Optional project ID to filter by

        Returns:
            List of StudyAttempt model instances
        """
        with self._get_db_session() as db:
            try:
                query = db.query(StudyAttempt).filter(StudyAttempt.user_id == user_id)

                if project_id:
                    query = query.filter(StudyAttempt.project_id == project_id)

                attempts = query.order_by(StudyAttempt.created_at.desc()).all()

                logger.info(
                    f"retrieved {len(attempts)} attempts for user_id={user_id}, project_id={project_id}"
                )

                return attempts
            except Exception as e:
                logger.error(
                    f"error retrieving attempts for user_id={user_id}, project_id={project_id}: {e}"
                )
                raise

    def _validate_item(self, db: Session, item_type: str, item_id: str) -> bool:
        """Validate that the referenced study resource exists.

        Args:
            db: Database session
            item_type: Type of study resource ('flashcard' or 'quiz')
            item_id: ID of the study resource to validate

        Returns:
            True if study resource exists, False otherwise
        """
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
            logger.error(
                f"error validating study resource item_id={item_id}, item_type={item_type}: {e}"
            )
            return False

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
