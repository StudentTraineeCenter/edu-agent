"""CRUD service for managing practice records."""

from contextlib import contextmanager
from uuid import uuid4

from edu_core.db.models import Flashcard, PracticeRecord, QuizQuestion
from edu_core.db.session import get_session_factory
from edu_core.schemas.practice import PracticeRecordDto


class PracticeService:
    """Service for managing practice records."""

    def __init__(self) -> None:
        """Initialize the practice service."""
        pass

    def create_practice_record(
        self,
        user_id: str,
        project_id: str,
        item_type: str,
        item_id: str,
        topic: str,
        user_answer: str | None,
        correct_answer: str,
        was_correct: bool,
    ) -> PracticeRecordDto:
        """Create a single practice record.

        Args:
            user_id: The user's unique identifier
            project_id: The project ID
            item_type: Type of study resource ('flashcard' or 'quiz')
            item_id: ID of the flashcard or quiz question
            topic: Topic of the study resource
            user_answer: User's answer (can be None for flashcards)
            correct_answer: The correct answer
            was_correct: Whether the user's answer was correct

        Returns:
            Created PracticeRecordDto

        Raises:
            ValueError: If the referenced study resource doesn't exist
        """
        with self._get_db_session() as db:
            try:
                # Validate that the referenced study resource exists
                if not self._validate_item(db, item_type, item_id):
                    raise ValueError(
                        f"Study resource {item_id} of type {item_type} not found"
                    )

                practice_record = PracticeRecord(
                    id=str(uuid4()),
                    user_id=user_id,
                    project_id=project_id,
                    item_type=item_type,
                    item_id=item_id,
                    topic=topic,
                    user_answer=user_answer,
                    correct_answer=correct_answer,
                    was_correct=was_correct,
                )

                db.add(practice_record)
                db.commit()
                db.refresh(practice_record)

                return self._model_to_dto(practice_record)
            except ValueError:
                raise
            except Exception:
                db.rollback()
                raise

    def create_practice_records_batch(
        self,
        user_id: str,
        project_id: str,
        practice_records_data: list[dict],
    ) -> list[PracticeRecordDto]:
        """Create multiple practice records in a batch.

        Args:
            user_id: The user's unique identifier
            project_id: The project ID
            practice_records_data: List of dictionaries containing practice record data

        Returns:
            List of created PracticeRecordDto instances
        """
        with self._get_db_session() as db:
            try:
                created_records = []

                for record_data in practice_records_data:
                    item_type = record_data.get("item_type")
                    item_id = record_data.get("item_id")

                    # Validate that the referenced study resource exists
                    if not self._validate_item(db, item_type, item_id):
                        continue

                    practice_record = PracticeRecord(
                        id=str(uuid4()),
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

                return [self._model_to_dto(record) for record in created_records]
            except Exception:
                db.rollback()
                raise

    def list_practice_records(
        self, user_id: str, project_id: str | None = None
    ) -> list[PracticeRecordDto]:
        """Retrieve practice records for a user, optionally filtered by project.

        Args:
            user_id: The user's unique identifier
            project_id: Optional project ID to filter by

        Returns:
            List of PracticeRecordDto instances
        """
        with self._get_db_session() as db:
            try:
                query = db.query(PracticeRecord).filter(
                    PracticeRecord.user_id == user_id
                )

                if project_id:
                    query = query.filter(PracticeRecord.project_id == project_id)

                records = query.order_by(PracticeRecord.created_at.desc()).all()

                return [self._model_to_dto(record) for record in records]
            except Exception:
                raise

    def _validate_item(self, db, item_type: str, item_id: str) -> bool:
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
        except Exception:
            return False

    def _model_to_dto(self, record: PracticeRecord) -> PracticeRecordDto:
        """Convert PracticeRecord model to PracticeRecordDto."""
        return PracticeRecordDto(
            id=record.id,
            user_id=record.user_id,
            project_id=record.project_id,
            item_type=record.item_type,
            item_id=record.item_id,
            topic=record.topic,
            user_answer=record.user_answer,
            correct_answer=record.correct_answer,
            was_correct=record.was_correct,
            created_at=record.created_at,
        )

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

