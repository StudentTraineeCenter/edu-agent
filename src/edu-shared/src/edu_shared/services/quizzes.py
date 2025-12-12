"""CRUD service for managing quizzes."""

from contextlib import contextmanager
from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from edu_shared.db.models import Quiz
from edu_shared.db.session import get_session_factory
from edu_shared.schemas.quizzes import QuizDto
from edu_shared.exceptions import NotFoundError


class QuizService:
    """Service for managing quizzes."""

    def __init__(self) -> None:
        """Initialize the quiz service."""
        pass

    def create_quiz(
        self,
        project_id: str,
        name: str,
        description: Optional[str] = None,
    ) -> QuizDto:
        """Create a new quiz.

        Args:
            project_id: The project ID
            name: The quiz name
            description: Optional quiz description

        Returns:
            Created QuizDto
        """
        with self._get_db_session() as db:
            try:
                quiz = Quiz(
                    id=str(uuid4()),
                    project_id=project_id,
                    name=name,
                    description=description,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
                db.add(quiz)
                db.commit()
                db.refresh(quiz)

                return self._model_to_dto(quiz)
            except Exception as e:
                db.rollback()
                raise

    def get_quiz(self, quiz_id: str, project_id: str) -> QuizDto:
        """Get a quiz by ID.

        Args:
            quiz_id: The quiz ID
            project_id: The project ID

        Returns:
            QuizDto

        Raises:
            NotFoundError: If quiz not found
        """
        with self._get_db_session() as db:
            try:
                quiz = (
                    db.query(Quiz)
                    .filter(Quiz.id == quiz_id, Quiz.project_id == project_id)
                    .first()
                )
                if not quiz:
                    raise NotFoundError(f"Quiz {quiz_id} not found")

                return self._model_to_dto(quiz)
            except NotFoundError:
                raise
            except Exception as e:
                raise

    def list_quizzes(self, project_id: str) -> List[QuizDto]:
        """List all quizzes for a project.

        Args:
            project_id: The project ID

        Returns:
            List of QuizDto instances
        """
        with self._get_db_session() as db:
            try:
                quizzes = (
                    db.query(Quiz)
                    .filter(Quiz.project_id == project_id)
                    .order_by(Quiz.created_at.desc())
                    .all()
                )
                return [self._model_to_dto(quiz) for quiz in quizzes]
            except Exception as e:
                raise

    def update_quiz(
        self,
        quiz_id: str,
        project_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> QuizDto:
        """Update a quiz.

        Args:
            quiz_id: The quiz ID
            project_id: The project ID
            name: Optional new name
            description: Optional new description

        Returns:
            Updated QuizDto

        Raises:
            NotFoundError: If quiz not found
        """
        with self._get_db_session() as db:
            try:
                quiz = (
                    db.query(Quiz)
                    .filter(Quiz.id == quiz_id, Quiz.project_id == project_id)
                    .first()
                )
                if not quiz:
                    raise NotFoundError(f"Quiz {quiz_id} not found")

                if name is not None:
                    quiz.name = name
                if description is not None:
                    quiz.description = description
                quiz.updated_at = datetime.now()

                db.commit()
                db.refresh(quiz)

                return self._model_to_dto(quiz)
            except NotFoundError:
                raise
            except Exception as e:
                db.rollback()
                raise

    def delete_quiz(self, quiz_id: str, project_id: str) -> None:
        """Delete a quiz.

        Args:
            quiz_id: The quiz ID
            project_id: The project ID

        Raises:
            NotFoundError: If quiz not found
        """
        with self._get_db_session() as db:
            try:
                quiz = (
                    db.query(Quiz)
                    .filter(Quiz.id == quiz_id, Quiz.project_id == project_id)
                    .first()
                )
                if not quiz:
                    raise NotFoundError(f"Quiz {quiz_id} not found")

                db.delete(quiz)
                db.commit()
            except NotFoundError:
                raise
            except Exception as e:
                db.rollback()
                raise

    def _model_to_dto(self, quiz: Quiz) -> QuizDto:
        """Convert Quiz model to QuizDto."""
        return QuizDto(
            id=quiz.id,
            project_id=quiz.project_id,
            name=quiz.name,
            description=quiz.description,
            created_at=quiz.created_at,
            updated_at=quiz.updated_at,
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

