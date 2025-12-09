"""Service for managing quizzes with AI generation capabilities."""

import uuid
from contextlib import contextmanager
from datetime import datetime
from typing import AsyncGenerator, List, Optional

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import AzureChatOpenAI
from sqlalchemy import func
from sqlalchemy.orm import Session

from core.agents.prompts_utils import render_prompt
from core.agents.search import SearchInterface
from core.config import app_config
from core.exceptions import BadRequestError, NotFoundError
from core.logger import get_logger
from db.models import Project, Quiz, QuizQuestion
from db.session import SessionLocal
from schemas.quizzes import (
    LENGTH_PREFERENCE_MAP,
    MAX_DOCUMENT_CONTENT_LENGTH,
    QuizAnswers,
    QuizGenerationRequest,
    QuizGenerationResult,
    QuizProgressUpdate,
    QuizQuestionData,
    QuizQuestionResult,
    QuizSubmissionResult,
    SEARCH_TOP_K_WITH_TOPIC,
    SEARCH_TOP_K_WITHOUT_TOPIC,
)
from schemas.shared import (
    CorrectOption,
    DifficultyLevel,
    GenerationProgressUpdate,
    GenerationStatus,
    LengthPreference,
)

logger = get_logger(__name__)


class QuizService:
    """Service for managing quizzes with AI generation capabilities."""

    def __init__(self, search_interface: SearchInterface) -> None:
        """Initialize the quiz service.

        Args:
            search_interface: Search interface for document retrieval
        """
        self.search_interface = search_interface
        self.credential = DefaultAzureCredential()
        self.token_provider = get_bearer_token_provider(
            self.credential, "https://cognitiveservices.azure.com/.default"
        )

        self.llm = AzureChatOpenAI(
            azure_deployment=app_config.AZURE_OPENAI_CHAT_DEPLOYMENT,
            azure_endpoint=app_config.AZURE_OPENAI_ENDPOINT,
            api_version="2024-12-01-preview",
            azure_ad_token_provider=self.token_provider,
            temperature=0.7,
        )

        self.quiz_parser = JsonOutputParser(pydantic_object=QuizGenerationRequest)

    def _resolve_count_from_length(
        self, length: Optional[LengthPreference]
    ) -> int:
        """Resolve length preference to question count.
        
        Args:
            length: Length preference enum or None
            
        Returns:
            Resolved question count
        """
        if length is None:
            length = LengthPreference.NORMAL
        return LENGTH_PREFERENCE_MAP[length]

    def _create_quiz_and_questions(
        self,
        db: Session,
        project_id: str,
        content: QuizGenerationResult,
    ) -> Quiz:
        """Create quiz and associated questions in database.
        
        Args:
            db: Database session
            project_id: The project ID
            content: Generated quiz content
            
        Returns:
            Created Quiz instance
        """
        quiz = Quiz(
            id=str(uuid.uuid4()),
            project_id=project_id,
            name=content.name,
            description=content.description,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.add(quiz)
        db.flush()

        for question_item in content.questions:
            quiz_question = QuizQuestion(
                id=str(uuid.uuid4()),
                quiz_id=quiz.id,
                project_id=project_id,
                question_text=question_item.question_text,
                option_a=question_item.option_a,
                option_b=question_item.option_b,
                option_c=question_item.option_c,
                option_d=question_item.option_d,
                correct_option=question_item.correct_option,
                explanation=question_item.explanation,
                difficulty_level=question_item.difficulty_level,
                created_at=datetime.now(),
            )
            db.add(quiz_question)

        return quiz

    async def create_quiz_with_questions(
        self,
        project_id: str,
        count: int = 30,
        custom_instructions: Optional[str] = None,
        length: Optional[LengthPreference] = None,
        difficulty: Optional[DifficultyLevel] = None,
    ) -> str:
        """Create a new quiz with auto-generated name, description, and questions.

        Args:
            project_id: The project ID
            count: Number of questions to generate (used if length is None)
            custom_instructions: Optional custom instructions including topic, format, length, and context
            length: Length preference enum
            difficulty: Difficulty level enum

        Returns:
            ID of the created quiz

        Raises:
            NotFoundError: If project not found
            ValueError: If no documents found or generation fails
        """
        with self._get_db_session() as db:
            try:
                resolved_count = (
                    self._resolve_count_from_length(length) if length else count
                )
                logger.info_structured(
                    "creating quiz",
                    project_id=project_id,
                    length=length.value if length else None,
                    count=resolved_count,
                    difficulty=difficulty.value if difficulty else None,
                )

                generated_content = await self._generate_quiz_content(
                    db=db,
                    project_id=project_id,
                    count=resolved_count,
                    custom_instructions=custom_instructions,
                    difficulty=difficulty,
                )

                logger.info_structured(
                    "generated quiz content",
                    project_id=project_id,
                    quiz_name=generated_content.name[:100] if generated_content.name else None,
                    question_count=len(generated_content.questions),
                )

                quiz = self._create_quiz_and_questions(
                    db=db,
                    project_id=project_id,
                    content=generated_content,
                )
                db.commit()

                logger.info_structured(
                    "created quiz",
                    quiz_id=quiz.id,
                    project_id=project_id,
                    question_count=len(generated_content.questions),
                )

                return str(quiz.id)
            except (NotFoundError, ValueError, BadRequestError):
                raise
            except Exception as e:
                logger.error_structured(
                    "error creating quiz",
                    project_id=project_id,
                    error=str(e),
                    exc_info=True,
                )
                raise

    async def create_quiz_with_questions_stream(
        self,
        project_id: str,
        count: int = 30,
        custom_instructions: Optional[str] = None,
        length: Optional[LengthPreference] = None,
        difficulty: Optional[DifficultyLevel] = None,
    ) -> AsyncGenerator[dict, None]:
        """Create a quiz with streaming progress updates.

        Args:
            project_id: The project ID
            count: Number of questions to generate (used if length is None)
            custom_instructions: Optional custom instructions including topic, format, length, and context
            length: Length preference enum
            difficulty: Difficulty level enum

        Yields:
            Progress update dictionaries with status and message
        """
        try:
            yield GenerationProgressUpdate(
                status=GenerationStatus.SEARCHING
            ).model_dump(exclude_none=True)

            with self._get_db_session() as db:
                project = db.query(Project).filter(Project.id == project_id).first()
                if not project:
                    yield GenerationProgressUpdate(
                        status=GenerationStatus.DONE,
                        error=f"Project {project_id} not found",
                    ).model_dump(exclude_none=True)
                    return

                yield GenerationProgressUpdate(
                    status=GenerationStatus.ANALYZING
                ).model_dump(exclude_none=True)

                document_content = await self._get_project_documents_content(
                    db=db,
                    project_id=project_id,
                    topic=custom_instructions,
                )
                if not document_content:
                    error_msg = (
                        f"No documents found related to '{custom_instructions}'. Please upload relevant documents or try a different topic."
                        if custom_instructions
                        else "No documents found in project. Please upload documents first."
                    )
                    yield GenerationProgressUpdate(
                        status=GenerationStatus.DONE,
                        error=error_msg,
                    ).model_dump(exclude_none=True)
                    return

                resolved_count = (
                    self._resolve_count_from_length(length) if length else count
                )
                yield GenerationProgressUpdate(
                    status=GenerationStatus.GENERATING
                ).model_dump(exclude_none=True)

                generated_content = await self._generate_quiz_content(
                    db=db,
                    project_id=project_id,
                    count=resolved_count,
                    custom_instructions=custom_instructions,
                    difficulty=difficulty,
                )

                quiz = self._create_quiz_and_questions(
                    db=db,
                    project_id=project_id,
                    content=generated_content,
                )
                db.commit()

                logger.info_structured(
                    "generated quiz",
                    quiz_id=quiz.id,
                    question_count=len(generated_content.questions),
                    project_id=project_id,
                )

                yield QuizProgressUpdate(
                    status=GenerationStatus.DONE,
                    quiz_id=str(quiz.id),
                ).model_dump(exclude_none=True)

        except (NotFoundError, ValueError, BadRequestError) as e:
            logger.error_structured(
                "error creating quiz",
                project_id=project_id,
                error=str(e),
            )
            yield GenerationProgressUpdate(
                status=GenerationStatus.DONE,
                error=str(e),
            ).model_dump(exclude_none=True)
        except Exception as e:
            logger.error_structured(
                "error creating quiz",
                project_id=project_id,
                error=str(e),
                exc_info=True,
            )
            yield GenerationProgressUpdate(
                status=GenerationStatus.DONE,
                error="Failed to create quiz. Please try again.",
            ).model_dump(exclude_none=True)

    def get_quizzes(self, project_id: str) -> List[Quiz]:
        """Get all quizzes for a project.

        Args:
            project_id: The project ID

        Returns:
            List of Quiz model instances
        """
        with self._get_db_session() as db:
            try:
                logger.info_structured("getting quizzes", project_id=project_id)

                quizzes = (
                    db.query(Quiz)
                    .filter(Quiz.project_id == project_id)
                    .order_by(Quiz.created_at.desc())
                    .all()
                )

                logger.info_structured("found quizzes", count=len(quizzes), project_id=project_id)
                return quizzes
            except Exception as e:
                logger.error_structured("error getting quizzes", project_id=project_id, error=str(e), exc_info=True)
                raise

    def get_quiz_questions(self, quiz_id: str) -> List[QuizQuestion]:
        """Get all questions in a quiz.

        Args:
            quiz_id: The quiz ID

        Returns:
            List of QuizQuestion model instances
        """
        with self._get_db_session() as db:
            try:
                logger.info_structured("getting quiz questions", quiz_id=quiz_id)

                questions = (
                    db.query(QuizQuestion)
                    .filter(QuizQuestion.quiz_id == quiz_id)
                    .order_by(QuizQuestion.position.asc())
                    .all()
                )

                logger.info_structured("found quiz questions", count=len(questions), quiz_id=quiz_id)
                return questions
            except Exception as e:
                logger.error_structured("error getting quiz questions", quiz_id=quiz_id, error=str(e), exc_info=True)
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
        correct_option: CorrectOption,
        explanation: Optional[str] = None,
        difficulty_level: DifficultyLevel = DifficultyLevel.MEDIUM,
        position: Optional[int] = None,
    ) -> QuizQuestion:
        """Create a new quiz question.

        Args:
            quiz_id: The quiz ID
            project_id: The project ID
            question_text: The question text
            option_a: Option A
            option_b: Option B
            option_c: Option C
            option_d: Option D
            correct_option: Correct option enum
            explanation: Optional explanation
            difficulty_level: Difficulty level enum
            position: Optional position for ordering. If None, appends to end.

        Returns:
            Created QuizQuestion model instance

        Raises:
            NotFoundError: If quiz not found
        """
        with self._get_db_session() as db:
            try:
                logger.info_structured(
                    "creating quiz question",
                    quiz_id=quiz_id,
                    project_id=project_id,
                )

                quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
                if not quiz:
                    raise NotFoundError(f"Quiz {quiz_id} not found")

                # If position not provided, get the max position and add 1
                if position is None:
                    max_position = (
                        db.query(func.max(QuizQuestion.position))
                        .filter(QuizQuestion.quiz_id == quiz_id)
                        .scalar()
                    )
                    position = (max_position or -1) + 1

                question = QuizQuestion(
                    id=str(uuid.uuid4()),
                    quiz_id=quiz_id,
                    project_id=project_id,
                    question_text=question_text,
                    option_a=option_a,
                    option_b=option_b,
                    option_c=option_c,
                    option_d=option_d,
                    correct_option=correct_option.value,
                    explanation=explanation,
                    difficulty_level=difficulty_level.value,
                    position=position,
                    created_at=datetime.now(),
                )

                db.add(question)
                db.commit()
                db.refresh(question)

                logger.info_structured("created quiz question", question_id=question.id, quiz_id=quiz_id, project_id=project_id)
                return question
            except (NotFoundError, ValueError):
                raise
            except Exception as e:
                logger.error_structured(
                    "error creating quiz question",
                    quiz_id=quiz_id,
                    project_id=project_id,
                    error=str(e),
                    exc_info=True,
                )
                raise

    def update_quiz_question(
        self,
        question_id: str,
        question_text: Optional[str] = None,
        option_a: Optional[str] = None,
        option_b: Optional[str] = None,
        option_c: Optional[str] = None,
        option_d: Optional[str] = None,
        correct_option: Optional[CorrectOption] = None,
        explanation: Optional[str] = None,
        difficulty_level: Optional[DifficultyLevel] = None,
    ) -> Optional[QuizQuestion]:
        """Update an existing quiz question.

        Args:
            question_id: The question ID
            question_text: Optional new question text
            option_a: Optional new option A
            option_b: Optional new option B
            option_c: Optional new option C
            option_d: Optional new option D
            correct_option: Optional new correct option
            explanation: Optional new explanation
            difficulty_level: Optional new difficulty level

        Returns:
            Updated QuizQuestion model instance or None if not found
        """
        with self._get_db_session() as db:
            try:
                logger.info_structured("updating quiz question", question_id=question_id, quiz_id=quiz_id)

                question = (
                    db.query(QuizQuestion)
                    .filter(QuizQuestion.id == question_id)
                    .first()
                )
                if not question:
                    logger.warning_structured("quiz question not found", question_id=question_id, quiz_id=quiz_id)
                    return None

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
                    question.correct_option = correct_option.value
                if explanation is not None:
                    question.explanation = explanation
                if difficulty_level is not None:
                    question.difficulty_level = difficulty_level.value

                db.commit()
                db.refresh(question)

                logger.info_structured(
                    "updated quiz question",
                    question_id=question_id,
                )
                return question
            except Exception as e:
                logger.error_structured(
                    "error updating quiz question",
                    question_id=question_id,
                    error=str(e),
                    exc_info=True,
                )
                raise

    def reorder_quiz_questions(
        self, quiz_id: str, question_ids: List[str]
    ) -> List[QuizQuestion]:
        """Reorder quiz questions in a quiz.

        Args:
            quiz_id: The quiz ID
            question_ids: List of question IDs in the desired order

        Returns:
            List of updated QuizQuestion model instances

        Raises:
            ValueError: If quiz not found or question IDs don't match quiz
        """
        with self._get_db_session() as db:
            try:
                logger.info_structured(
                    "reordering quiz questions",
                    quiz_id=quiz_id,
                    question_count=len(question_ids),
                )

                quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
                if not quiz:
                    raise NotFoundError(f"Quiz {quiz_id} not found")

                # Get all questions in the quiz
                questions = (
                    db.query(QuizQuestion).filter(QuizQuestion.quiz_id == quiz_id).all()
                )
                question_dict = {q.id: q for q in questions}

                for question_id in question_ids:
                    if question_id not in question_dict:
                        raise NotFoundError(
                            f"Quiz question {question_id} not found in quiz {quiz_id}"
                        )

                # Update positions based on the order in question_ids
                updated_questions = []
                for position, question_id in enumerate(question_ids):
                    question = question_dict[question_id]
                    question.position = position
                    updated_questions.append(question)

                db.commit()
                for question in updated_questions:
                    db.refresh(question)

                logger.info_structured(
                    "reordered quiz questions",
                    count=len(updated_questions),
                    quiz_id=quiz_id,
                )
                return updated_questions
            except (NotFoundError, ValueError):
                raise
            except Exception as e:
                logger.error_structured(
                    "error reordering quiz questions",
                    quiz_id=quiz_id,
                    error=str(e),
                    exc_info=True,
                )
                raise

    def delete_quiz_question(self, question_id: str) -> bool:
        """Delete a quiz question.

        Args:
            question_id: The question ID

        Returns:
            True if deleted successfully, False if not found
        """
        with self._get_db_session() as db:
            try:
                logger.info_structured("deleting quiz question", question_id=question_id, quiz_id=quiz_id)

                question = (
                    db.query(QuizQuestion)
                    .filter(QuizQuestion.id == question_id)
                    .first()
                )

                if not question:
                    logger.warning_structured("quiz question not found", question_id=question_id, quiz_id=quiz_id)
                    return False

                db.delete(question)
                db.commit()

                logger.info_structured(
                    "deleted quiz question",
                    question_id=question_id,
                )
                return True
            except Exception as e:
                logger.error_structured(
                    "error deleting quiz question",
                    question_id=question_id,
                    error=str(e),
                    exc_info=True,
                )
                raise

    def get_quiz(self, quiz_id: str) -> Quiz:
        """Get a specific quiz by ID.

        Args:
            quiz_id: The quiz ID

        Returns:
            Quiz model instance

        Raises:
            NotFoundError: If quiz not found
        """
        with self._get_db_session() as db:
            try:
                logger.info_structured("getting quiz", quiz_id=quiz_id)

                quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
                if not quiz:
                    raise NotFoundError(f"Quiz {quiz_id} not found")

                logger.info_structured("found quiz", quiz_id=quiz_id)
                return quiz
            except NotFoundError:
                raise
            except Exception as e:
                logger.error_structured(
                    "error getting quiz",
                    quiz_id=quiz_id,
                    error=str(e),
                    exc_info=True,
                )
                raise

    def update_quiz(
        self,
        quiz_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Quiz:
        """Update a quiz.

        Args:
            quiz_id: The quiz ID
            name: Optional new name
            description: Optional new description

        Returns:
            Updated Quiz model instance

        Raises:
            NotFoundError: If quiz not found
        """
        with self._get_db_session() as db:
            try:
                logger.info_structured("updating quiz", quiz_id=quiz_id)

                quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
                if not quiz:
                    raise NotFoundError(f"Quiz {quiz_id} not found")

                if name is not None:
                    quiz.name = name
                if description is not None:
                    quiz.description = description
                quiz.updated_at = datetime.now()
                db.commit()
                db.refresh(quiz)

                logger.info_structured("updated quiz", quiz_id=quiz_id)
                return quiz
            except NotFoundError:
                raise
            except Exception as e:
                logger.error_structured(
                    "error updating quiz",
                    quiz_id=quiz_id,
                    error=str(e),
                    exc_info=True,
                )
                raise

    def delete_quiz(self, quiz_id: str) -> bool:
        """Delete a quiz and all its questions.

        Args:
            quiz_id: The quiz ID

        Returns:
            True if deleted successfully

        Raises:
            NotFoundError: If quiz not found
        """
        with self._get_db_session() as db:
            try:
                logger.info_structured("deleting quiz", quiz_id=quiz_id)

                quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
                if not quiz:
                    raise NotFoundError(f"Quiz {quiz_id} not found")

                db.delete(quiz)
                db.commit()

                logger.info_structured("deleted quiz", quiz_id=quiz_id)
                return True
            except NotFoundError:
                raise
            except Exception as e:
                logger.error_structured(
                    "error deleting quiz",
                    quiz_id=quiz_id,
                    error=str(e),
                    exc_info=True,
                )
                raise

    async def submit_quiz_answers(
        self, quiz_id: str, answers: QuizAnswers
    ) -> QuizSubmissionResult:
        """Submit quiz answers and get results.

        Args:
            quiz_id: The quiz ID
            answers: QuizAnswers containing mapping of question IDs to user answers

        Returns:
            QuizSubmissionResult containing quiz results

        Raises:
            ValueError: If quiz or questions not found
        """
        with self._get_db_session() as db:
            try:
                logger.info_structured("submitting answers", quiz_id=quiz_id)

                # Get all questions for the quiz
                questions = (
                    db.query(QuizQuestion).filter(QuizQuestion.quiz_id == quiz_id).all()
                )

                if not questions:
                    raise ValueError(f"No questions found for quiz {quiz_id}")

                # Calculate results
                total_questions = len(questions)
                correct_answers = 0
                question_results = []

                for question in questions:
                    user_answer = answers.answers.get(question.id, "")
                    is_correct = user_answer.lower() == question.correct_option.lower()

                    if is_correct:
                        correct_answers += 1

                    question_results.append(
                        QuizQuestionResult(
                            question_id=question.id,
                            question_text=question.question_text,
                            user_answer=user_answer,
                            correct_answer=question.correct_option,
                            is_correct=is_correct,
                            explanation=question.explanation,
                            difficulty_level=question.difficulty_level,
                        )
                    )

                # Calculate score
                score_percentage = (correct_answers / total_questions) * 100

                # Determine grade
                if score_percentage >= 90:
                    grade = "A"
                elif score_percentage >= 80:
                    grade = "B"
                elif score_percentage >= 70:
                    grade = "C"
                elif score_percentage >= 60:
                    grade = "D"
                else:
                    grade = "F"

                quiz_result = QuizSubmissionResult(
                    quiz_id=quiz_id,
                    total_questions=total_questions,
                    correct_answers=correct_answers,
                    score_percentage=round(score_percentage, 2),
                    grade=grade,
                    results=question_results,
                    submitted_at=datetime.now().isoformat(),
                )

                logger.info_structured(
                    "quiz completed",
                    quiz_id=quiz_id,
                    correct_answers=correct_answers,
                    total_questions=total_questions,
                    score_percentage=round(score_percentage, 2),
                )
                return quiz_result
            except (NotFoundError, ValueError):
                raise
            except Exception as e:
                logger.error_structured(
                    "error submitting quiz answers",
                    quiz_id=quiz_id,
                    error=str(e),
                    exc_info=True,
                )
                raise

    async def _generate_quiz_content(
        self,
        db: Session,
        project_id: str,
        count: int = 30,
        custom_instructions: Optional[str] = None,
        difficulty: Optional[DifficultyLevel] = None,
    ) -> QuizGenerationResult:
        """Generate quiz name, description, and questions in one call.

        Args:
            db: Database session
            project_id: The project ID
            count: Number of questions to generate
            custom_instructions: Optional custom instructions including topic, format, length, and context
            difficulty: Difficulty level enum

        Returns:
            QuizGenerationResult containing name, description, and questions

        Raises:
            NotFoundError: If project not found
            ValueError: If no documents available
        """
        try:
            logger.info_structured(
                "generating quiz content",
                project_id=project_id,
                count=count,
                difficulty=difficulty.value if difficulty else None,
            )

            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                raise NotFoundError(f"Project {project_id} not found")

            language_code = project.language_code
            logger.info_structured(
                "using language code",
                language_code=language_code,
                project_id=project_id,
            )

            document_content = await self._get_project_documents_content(
                db=db,
                project_id=project_id,
                topic=custom_instructions,
            )
            if not document_content:
                error_msg = (
                    f"No documents found related to '{custom_instructions}'. Please upload relevant documents or try a different topic."
                    if custom_instructions
                    else "No documents found in project. Please upload documents first."
                )
                raise ValueError(error_msg)

            logger.info_structured(
                "found document content",
                document_content_length=len(document_content),
                project_id=project_id,
            )

            difficulty_instruction = ""
            if difficulty == DifficultyLevel.EASY:
                difficulty_instruction = " Focus on basic concepts and straightforward questions suitable for beginners."
            elif difficulty == DifficultyLevel.HARD:
                difficulty_instruction = " Create challenging questions that test deep understanding, analysis, and application of concepts."

            prompt = render_prompt(
                "quiz_prompt",
                document_content=document_content[:MAX_DOCUMENT_CONTENT_LENGTH],
                count=count,
                custom_instructions=(custom_instructions
                or "Generate comprehensive quiz questions covering key concepts, definitions, and important details.")
                + difficulty_instruction,
                language_code=language_code,
                format_instructions=self.quiz_parser.get_format_instructions(),
            )

            response = await self.llm.ainvoke(prompt)
            parsed_dict = self.quiz_parser.parse(response.content)
            generation_request = QuizGenerationRequest(**parsed_dict)

            return QuizGenerationResult(
                name=generation_request.name,
                description=generation_request.description,
                questions=generation_request.questions,
            )
        except (NotFoundError, ValueError):
            raise
        except Exception as e:
            logger.error_structured(
                "error generating quiz content",
                project_id=project_id,
                error=str(e),
                exc_info=True,
            )
            raise

    async def _get_project_documents_content(
        self,
        db: Session,
        project_id: str,
        topic: Optional[str] = None,
    ) -> str:
        """Get document content for a project, optionally filtered by topic.

        Args:
            db: Database session
            project_id: The project ID
            topic: Optional topic to filter documents by

        Returns:
            Combined document content as string
        """
        try:
            query = topic or ""
            top_k = (
                SEARCH_TOP_K_WITH_TOPIC if topic else SEARCH_TOP_K_WITHOUT_TOPIC
            )

            logger.info_structured(
                "searching documents",
                project_id=project_id,
                has_topic=bool(topic),
                top_k=top_k,
            )

            search_results = await self.search_interface.search_documents(
                query=query,
                project_id=project_id,
                top_k=top_k,
            )

            if not search_results:
                logger.warning_structured(
                    "no search results found",
                    project_id=project_id,
                    has_topic=bool(topic),
                )
                return ""

            content = "\n\n".join(result.content for result in search_results)
            logger.info_structured(
                "retrieved document content",
                project_id=project_id,
                result_count=len(search_results),
                content_length=len(content),
            )
            return content
        except Exception as e:
            logger.error_structured(
                "error getting project documents content",
                project_id=project_id,
                error=str(e),
                exc_info=True,
            )
            return ""


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
