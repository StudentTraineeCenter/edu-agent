"""CRUD service for managing quizzes."""

from contextlib import contextmanager
from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from edu_shared.db.models import Quiz, QuizQuestion
from edu_shared.db.session import get_session_factory
from edu_shared.schemas.quizzes import QuizDto
from edu_shared.exceptions import NotFoundError
from edu_shared.agents.quiz_agent import QuizAgent
from edu_shared.agents.base import ContentAgentConfig
from edu_shared.services.search import SearchService


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

    async def generate_and_populate(
        self,
        quiz_id: str,
        project_id: str,
        search_service: SearchService,
        agent_config: ContentAgentConfig,
        topic: Optional[str] = None,
        custom_instructions: Optional[str] = None,
    ) -> QuizDto:
        """Generate quiz questions using AI and populate an existing quiz.
        
        Args:
            quiz_id: The quiz ID to populate
            project_id: The project ID
            search_service: SearchService instance for RAG
            agent_config: ContentAgentConfig for AI generation
            topic: Optional topic for generation
            custom_instructions: Optional custom instructions
            
        Returns:
            Updated QuizDto
            
        Raises:
            NotFoundError: If quiz not found
        """
        with self._get_db_session() as db:
            try:
                # Find existing quiz
                quiz = db.query(Quiz).filter(
                    Quiz.id == quiz_id,
                    Quiz.project_id == project_id,
                ).first()
                if not quiz:
                    raise NotFoundError(f"Quiz {quiz_id} not found")

                # Generate quiz using AI
                quiz_agent = QuizAgent(config=agent_config, search_service=search_service)
                result = await quiz_agent.generate(
                    project_id=project_id,
                    topic=topic or "",
                    custom_instructions=custom_instructions,
                )

                # Update quiz with generated name and description
                quiz.name = result.name
                quiz.description = result.description
                quiz.updated_at = datetime.now()
                db.flush()

                # Delete existing questions and create new ones
                db.query(QuizQuestion).filter(QuizQuestion.quiz_id == quiz_id).delete()

                # Save quiz questions
                for position, question_item in enumerate(result.questions):
                    quiz_question = QuizQuestion(
                        id=str(uuid4()),
                        quiz_id=quiz_id,
                        project_id=project_id,
                        question_text=question_item.question_text,
                        option_a=question_item.option_a,
                        option_b=question_item.option_b,
                        option_c=question_item.option_c,
                        option_d=question_item.option_d,
                        correct_option=question_item.correct_option,
                        explanation=question_item.explanation,
                        difficulty_level=question_item.difficulty_level,
                        position=position,
                        created_at=datetime.now(),
                    )
                    db.add(quiz_question)

                db.commit()
                db.refresh(quiz)

                return self._model_to_dto(quiz)
            except NotFoundError:
                raise
            except Exception as e:
                db.rollback()
                raise

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

