"""Service for managing practice records."""

from contextlib import contextmanager
from typing import List

from sqlalchemy.orm import Session

from core.logger import get_logger
from db.models import Flashcard, PracticeRecord, QuizQuestion
from db.session import SessionLocal

logger = get_logger(__name__)


class PracticeService:
    """Service for managing practice records."""

    def __init__(self) -> None:
        """Initialize the practice service."""
        pass

    def create_practice_record(
        self,
        user_id: str,
        project_id: str,
        study_resource_type: str,
        study_resource_id: str,
        topic: str,
        user_answer: str | None,
        correct_answer: str,
        was_correct: bool,
    ) -> PracticeRecord:
        """Create a single practice record.

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
            Created PracticeRecord model instance

        Raises:
            ValueError: If the referenced study resource doesn't exist
        """
        with self._get_db_session() as db:
            try:
                # Validate that the referenced study resource exists
                if not self._validate_item(db, study_resource_type, study_resource_id):
                    raise ValueError(
                        f"Study resource {study_resource_id} of type {study_resource_type} not found"
                    )

                practice_record = PracticeRecord(
                    user_id=user_id,
                    project_id=project_id,
                    item_type=study_resource_type,
                    item_id=study_resource_id,
                    topic=topic,
                    user_answer=user_answer,
                    correct_answer=correct_answer,
                    was_correct=was_correct,
                )

                db.add(practice_record)
                db.commit()
                db.refresh(practice_record)

                # If flashcard, update progress
                if study_resource_type == "flashcard":
                    from core.services.flashcard_progress import (
                        FlashcardProgressService,
                    )
                    from db.models import Flashcard

                    progress_service = FlashcardProgressService()
                    flashcard = (
                        db.query(Flashcard)
                        .filter(Flashcard.id == study_resource_id)
                        .first()
                    )
                    if flashcard:
                        progress_service.record_answer(
                            db=db,
                            user_id=user_id,
                            flashcard_id=study_resource_id,
                            group_id=flashcard.group_id,
                            project_id=project_id,
                            is_correct=was_correct,
                        )

                logger.info(
                    f"created practice record id={practice_record.id} for user_id={user_id}, item_type={study_resource_type}, item_id={study_resource_id}"
                )

                return practice_record
            except ValueError:
                raise
            except Exception as e:
                logger.error(
                    f"error creating practice record for user_id={user_id}, item_id={study_resource_id}: {e}"
                )
                raise

    def create_practice_records_batch(
        self,
        user_id: str,
        project_id: str,
        practice_records_data: List[dict],
    ) -> List[PracticeRecord]:
        """Create multiple practice records in a batch.

        Args:
            user_id: The user's unique identifier
            project_id: The project ID
            practice_records_data: List of dictionaries containing practice record data

        Returns:
            List of created PracticeRecord model instances
        """
        with self._get_db_session() as db:
            try:
                created_records = []

                for record_data in practice_records_data:
                    item_type = record_data.get("item_type")
                    item_id = record_data.get("item_id")

                    # Validate that the referenced study resource exists
                    if not self._validate_item(db, item_type, item_id):
                        logger.warning(
                            f"skipping practice record: study resource {item_id} of type {item_type} not found"
                        )
                        continue

                    practice_record = PracticeRecord(
                        user_id=user_id,
                        project_id=project_id,
                        item_type=item_type,
                        item_id=item_id,
                        topic=record_data.get("topic"),
                        user_answer=record_data.get("user_answer"),
                        correct_answer=record_data.get("correct_answer"),
                        was_correct=record_data.get("was_correct"),
                    )

                    db.add(practice_record)
                    created_records.append(practice_record)

                db.commit()

                # Refresh all records
                for record in created_records:
                    db.refresh(record)

                logger.info(
                    f"created {len(created_records)} practice records for user_id={user_id}, project_id={project_id}"
                )

                return created_records
            except Exception as e:
                logger.error(
                    f"error creating practice records batch for user_id={user_id}, project_id={project_id}: {e}"
                )
                raise

    def get_user_practice_records(
        self, user_id: str, project_id: str | None = None
    ) -> List[PracticeRecord]:
        """Retrieve practice records for a user, optionally filtered by project.

        Args:
            user_id: The user's unique identifier
            project_id: Optional project ID to filter by

        Returns:
            List of PracticeRecord model instances
        """
        with self._get_db_session() as db:
            try:
                query = db.query(PracticeRecord).filter(
                    PracticeRecord.user_id == user_id
                )

                if project_id:
                    query = query.filter(PracticeRecord.project_id == project_id)

                records = query.order_by(PracticeRecord.created_at.desc()).all()

                logger.info(
                    f"retrieved {len(records)} practice records for user_id={user_id}, project_id={project_id}"
                )

                return records
            except Exception as e:
                logger.error(
                    f"error retrieving practice records for user_id={user_id}, project_id={project_id}: {e}"
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
