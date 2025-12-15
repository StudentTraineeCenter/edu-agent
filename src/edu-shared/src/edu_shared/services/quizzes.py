"""CRUD service for managing quizzes."""

from contextlib import contextmanager
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from langchain_openai import AzureChatOpenAI

from edu_shared.agents.base import ContentAgentConfig
from edu_shared.agents.quiz_agent import QuizAgent
from edu_shared.db.models import Project, Quiz, QuizQuestion
from edu_shared.db.session import get_session_factory
from edu_shared.exceptions import NotFoundError
from edu_shared.schemas.quizzes import QuizDto, QuizQuestionDto
from edu_shared.services.search import SearchService

if TYPE_CHECKING:
    from edu_shared.services.queue import QueueService

class QuizService:
    """Service for managing quizzes."""

    def __init__(self) -> None:
        """Initialize the quiz service."""
        pass

    def create_quiz(
        self,
        project_id: str,
        name: str,
        description: str | None = None,
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
            except Exception:
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
            except Exception:
                raise

    def list_quizzes(self, project_id: str) -> list[QuizDto]:
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
            except Exception:
                raise

    def update_quiz(
        self,
        quiz_id: str,
        project_id: str,
        name: str | None = None,
        description: str | None = None,
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
            except Exception:
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
            except Exception:
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
        llm: AzureChatOpenAI | None = None,
        agent_config: ContentAgentConfig | None = None,
        topic: str | None = None,
        custom_instructions: str | None = None,
        count: int | None = None,
    ) -> QuizDto:
        """Generate quiz questions using AI and populate an existing quiz.
        
        Args:
            quiz_id: The quiz ID to populate
            project_id: The project ID
            search_service: SearchService instance for RAG
            agent_config: ContentAgentConfig for AI generation
            topic: Optional topic for generation
            custom_instructions: Optional custom instructions
            count: Optional count of questions to generate
            
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

                # Get project language code
                project = db.query(Project).filter(Project.id == project_id).first()
                if not project:
                    raise NotFoundError(f"Project {project_id} not found")
                language_code = project.language_code

                # Generate quiz using AI
                quiz_agent = QuizAgent(
                    search_service=search_service,
                    llm=llm,
                    config=agent_config,
                )
                kwargs = {}
                if count is not None:
                    kwargs["count"] = count
                result = await quiz_agent.generate(
                    project_id=project_id,
                    topic=topic or "",
                    language_code=language_code,
                    custom_instructions=custom_instructions,
                    **kwargs,
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
            except Exception:
                db.rollback()
                raise

    def create_quiz_question(
        self,
        quiz_id: str,
        project_id: str,
        question_text: str,
        option_a: str,
        option_b: str,
        option_c: str,
        option_d: str,
        correct_option: str,
        explanation: str | None = None,
        difficulty_level: str = "medium",
        position: int | None = None,
    ) -> QuizQuestionDto:
        """Create a new quiz question.

        Args:
            quiz_id: The quiz ID
            project_id: The project ID
            question_text: The question text
            option_a: Option A
            option_b: Option B
            option_c: Option C
            option_d: Option D
            correct_option: Correct option (a, b, c, or d)
            explanation: Optional explanation
            difficulty_level: Difficulty level (easy, medium, hard)
            position: Optional position for ordering (auto-assigned if None)

        Returns:
            Created QuizQuestionDto

        Raises:
            NotFoundError: If quiz not found
        """
        with self._get_db_session() as db:
            try:
                # Verify quiz exists
                quiz = (
                    db.query(Quiz)
                    .filter(Quiz.id == quiz_id, Quiz.project_id == project_id)
                    .first()
                )
                if not quiz:
                    raise NotFoundError(f"Quiz {quiz_id} not found")

                # Auto-assign position if not provided
                if position is None:
                    max_position = (
                        db.query(QuizQuestion.position)
                        .filter(QuizQuestion.quiz_id == quiz_id)
                        .order_by(QuizQuestion.position.desc())
                        .limit(1)
                        .scalar()
                    )
                    position = (max_position + 1) if max_position is not None else 0

                question = QuizQuestion(
                    id=str(uuid4()),
                    quiz_id=quiz_id,
                    project_id=project_id,
                    question_text=question_text,
                    option_a=option_a,
                    option_b=option_b,
                    option_c=option_c,
                    option_d=option_d,
                    correct_option=correct_option,
                    explanation=explanation,
                    difficulty_level=difficulty_level,
                    position=position,
                    created_at=datetime.now(),
                )
                db.add(question)
                db.commit()
                db.refresh(question)

                return self._question_model_to_dto(question)
            except NotFoundError:
                raise
            except Exception:
                db.rollback()
                raise

    def get_quiz_question(
        self, question_id: str, quiz_id: str, project_id: str
    ) -> QuizQuestionDto:
        """Get a quiz question by ID.

        Args:
            question_id: The question ID
            quiz_id: The quiz ID
            project_id: The project ID

        Returns:
            QuizQuestionDto

        Raises:
            NotFoundError: If question not found
        """
        with self._get_db_session() as db:
            try:
                question = (
                    db.query(QuizQuestion)
                    .filter(
                        QuizQuestion.id == question_id,
                        QuizQuestion.quiz_id == quiz_id,
                        QuizQuestion.project_id == project_id,
                    )
                    .first()
                )
                if not question:
                    raise NotFoundError(f"Quiz question {question_id} not found")

                return self._question_model_to_dto(question)
            except NotFoundError:
                raise
            except Exception:
                raise

    def list_quiz_questions(
        self, quiz_id: str, project_id: str
    ) -> list[QuizQuestionDto]:
        """List all questions in a quiz.

        Args:
            quiz_id: The quiz ID
            project_id: The project ID

        Returns:
            List of QuizQuestionDto instances
        """
        with self._get_db_session() as db:
            try:
                questions = (
                    db.query(QuizQuestion)
                    .filter(
                        QuizQuestion.quiz_id == quiz_id,
                        QuizQuestion.project_id == project_id,
                    )
                    .order_by(QuizQuestion.position.asc())
                    .all()
                )
                return [self._question_model_to_dto(q) for q in questions]
            except Exception:
                raise

    def update_quiz_question(
        self,
        question_id: str,
        quiz_id: str,
        project_id: str,
        question_text: str | None = None,
        option_a: str | None = None,
        option_b: str | None = None,
        option_c: str | None = None,
        option_d: str | None = None,
        correct_option: str | None = None,
        explanation: str | None = None,
        difficulty_level: str | None = None,
        position: int | None = None,
    ) -> QuizQuestionDto:
        """Update a quiz question.

        Args:
            question_id: The question ID
            quiz_id: The quiz ID
            project_id: The project ID
            question_text: Optional new question text
            option_a: Optional new option A
            option_b: Optional new option B
            option_c: Optional new option C
            option_d: Optional new option D
            correct_option: Optional new correct option
            explanation: Optional new explanation
            difficulty_level: Optional new difficulty level
            position: Optional new position

        Returns:
            Updated QuizQuestionDto

        Raises:
            NotFoundError: If question not found
        """
        with self._get_db_session() as db:
            try:
                question = (
                    db.query(QuizQuestion)
                    .filter(
                        QuizQuestion.id == question_id,
                        QuizQuestion.quiz_id == quiz_id,
                        QuizQuestion.project_id == project_id,
                    )
                    .first()
                )
                if not question:
                    raise NotFoundError(f"Quiz question {question_id} not found")

                if question_text is not None:
                    question.question_text = question_text
                if option_a is not None:
                    question.option_a = option_a
                if option_b is not None:
                    question.option_b = option_b
                if option_c is not None:
                    question.option_c = option_c
                if option_d is not None:
                    question.option_d = option_d
                if correct_option is not None:
                    question.correct_option = correct_option
                if explanation is not None:
                    question.explanation = explanation
                if difficulty_level is not None:
                    question.difficulty_level = difficulty_level
                if position is not None:
                    question.position = position

                db.commit()
                db.refresh(question)

                return self._question_model_to_dto(question)
            except NotFoundError:
                raise
            except Exception:
                db.rollback()
                raise

    def delete_quiz_question(
        self, question_id: str, quiz_id: str, project_id: str
    ) -> None:
        """Delete a quiz question.

        Args:
            question_id: The question ID
            quiz_id: The quiz ID
            project_id: The project ID

        Raises:
            NotFoundError: If question not found
        """
        with self._get_db_session() as db:
            try:
                question = (
                    db.query(QuizQuestion)
                    .filter(
                        QuizQuestion.id == question_id,
                        QuizQuestion.quiz_id == quiz_id,
                        QuizQuestion.project_id == project_id,
                    )
                    .first()
                )
                if not question:
                    raise NotFoundError(f"Quiz question {question_id} not found")

                db.delete(question)
                db.commit()
            except NotFoundError:
                raise
            except Exception:
                db.rollback()
                raise

    def reorder_quiz_questions(
        self, quiz_id: str, project_id: str, question_ids: list[str]
    ) -> list[QuizQuestionDto]:
        """Reorder quiz questions.

        Args:
            quiz_id: The quiz ID
            project_id: The project ID
            question_ids: List of question IDs in the desired order

        Returns:
            List of updated QuizQuestionDto instances

        Raises:
            NotFoundError: If quiz or any question not found
        """
        with self._get_db_session() as db:
            try:
                # Verify quiz exists
                quiz = (
                    db.query(Quiz)
                    .filter(Quiz.id == quiz_id, Quiz.project_id == project_id)
                    .first()
                )
                if not quiz:
                    raise NotFoundError(f"Quiz {quiz_id} not found")

                # Update positions
                questions = []
                for position, question_id in enumerate(question_ids):
                    question = (
                        db.query(QuizQuestion)
                        .filter(
                            QuizQuestion.id == question_id,
                            QuizQuestion.quiz_id == quiz_id,
                            QuizQuestion.project_id == project_id,
                        )
                        .first()
                    )
                    if not question:
                        raise NotFoundError(f"Quiz question {question_id} not found")
                    question.position = position
                    questions.append(question)

                db.commit()
                for q in questions:
                    db.refresh(q)

                return [self._question_model_to_dto(q) for q in questions]
            except NotFoundError:
                raise
            except Exception:
                db.rollback()
                raise

    def _question_model_to_dto(self, question: QuizQuestion) -> QuizQuestionDto:
        """Convert QuizQuestion model to QuizQuestionDto."""
        return QuizQuestionDto(
            id=question.id,
            quiz_id=question.quiz_id,
            project_id=question.project_id,
            question_text=question.question_text,
            option_a=question.option_a,
            option_b=question.option_b,
            option_c=question.option_c,
            option_d=question.option_d,
            correct_option=question.correct_option,
            explanation=question.explanation,
            difficulty_level=question.difficulty_level,
            position=question.position,
            created_at=question.created_at,
        )

    def queue_generation(
        self,
        quiz_id: str,
        project_id: str,
        queue_service: "QueueService",
        topic: str | None = None,
        custom_instructions: str | None = None,
        count: int | None = None,
        user_id: str | None = None,
    ) -> QuizDto:
        """Queue a quiz generation request to be processed by a worker.
        
        Args:
            quiz_id: The quiz ID to populate
            project_id: The project ID
            queue_service: QueueService instance to send the message
            topic: Optional topic for generation
            custom_instructions: Optional custom instructions
            count: Optional count of questions to generate
            user_id: Optional user ID for queue message
            
        Returns:
            Existing QuizDto (generation will happen asynchronously)
            
        Raises:
            NotFoundError: If quiz not found
        """
        from edu_shared.schemas.queue import (
            QueueTaskMessage,
            QuizGenerationData,
            TaskType,
        )

        # Verify quiz exists
        quiz = self.get_quiz(quiz_id=quiz_id, project_id=project_id)

        # Prepare task data
        task_data: QuizGenerationData = {
            "project_id": project_id,
            "quiz_id": quiz_id,
        }
        if topic:
            task_data["topic"] = topic
        if custom_instructions:
            task_data["custom_instructions"] = custom_instructions
        if user_id:
            task_data["user_id"] = user_id
        if count is not None:
            task_data["count"] = count

        # Send message to queue
        task_message: QueueTaskMessage = {
            "type": TaskType.QUIZ_GENERATION,
            "data": task_data,
        }
        queue_service.send_message(task_message)

        return quiz

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

