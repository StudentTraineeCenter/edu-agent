"""Service for managing quizzes with AI generation capabilities."""

import uuid
from contextlib import contextmanager
from datetime import datetime
from typing import AsyncGenerator, List, Optional

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import AzureChatOpenAI
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from core.agents.search import SearchInterface
from core.config import app_config
from core.logger import get_logger
from db.models import Project, Quiz, QuizQuestion
from db.session import SessionLocal

logger = get_logger(__name__)


class QuizQuestionData(BaseModel):
    """Pydantic model for quiz question data structure."""

    question_text: str = Field(description="The quiz question text")
    option_a: str = Field(description="Option A")
    option_b: str = Field(description="Option B")
    option_c: str = Field(description="Option C")
    option_d: str = Field(description="Option D")
    correct_option: str = Field(description="Correct option: a, b, c, or d")
    explanation: str = Field(description="Explanation for the correct answer")
    difficulty_level: str = Field(description="Difficulty level: easy, medium, or hard")


class QuizGenerationRequest(BaseModel):
    """Pydantic model for quiz generation request."""

    name: str = Field(description="Generated name for the quiz")
    description: str = Field(description="Generated description for the quiz")
    questions: List[QuizQuestionData] = Field(
        description="List of generated quiz questions"
    )


class QuizGenerationResult(BaseModel):
    """Model for quiz generation result."""

    name: str
    description: str
    questions: List[QuizQuestionData]


class QuizAnswers(BaseModel):
    """Model for quiz answers submission."""

    answers: dict[str, str] = Field(
        description="Mapping of question IDs to user answers"
    )


class QuizQuestionResult(BaseModel):
    """Model for individual question result."""

    question_id: str
    question_text: str
    user_answer: str
    correct_answer: str
    is_correct: bool
    explanation: str
    difficulty_level: str


class QuizSubmissionResult(BaseModel):
    """Model for quiz submission result."""

    quiz_id: str
    total_questions: int
    correct_answers: int
    score_percentage: float
    grade: str
    results: List[QuizQuestionResult]
    submitted_at: str


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

    async def create_quiz_with_questions(
        self,
        project_id: str,
        count: int = 30,
        user_prompt: Optional[str] = None,
    ) -> str:
        """Create a new quiz with auto-generated name, description, and questions.

        Args:
            project_id: The project ID
            count: Number of questions to generate
            user_prompt: Optional user instructions for generation

        Returns:
            ID of the created quiz

        Raises:
            ValueError: If no documents found or generation fails
        """
        with self._get_db_session() as db:
            try:
                logger.info(
                    f"creating quiz with count={count} questions for project_id={project_id}"
                )

                # Generate all content using LangChain directly
                generated_content = await self._generate_quiz_content(
                    db=db,
                    project_id=project_id,
                    count=count,
                    user_prompt=user_prompt,
                )

                name = generated_content.name
                description = generated_content.description
                questions_data = generated_content.questions

                logger.info(
                    f"creating quiz name='{name[:100]}...' for project_id={project_id}"
                )

                quiz = Quiz(
                    id=str(uuid.uuid4()),
                    project_id=project_id,
                    name=name,
                    description=description,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )

                db.add(quiz)

                logger.info(f"created quiz_id={quiz.id}")

                # Save quiz questions to database
                for question_item in questions_data:
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

                db.commit()

                logger.info(f"generated {len(questions_data)} quiz questions")

                return str(quiz.id)
            except ValueError:
                raise
            except Exception as e:
                logger.error(f"error creating quiz for project_id={project_id}: {e}")
                raise

    async def create_quiz_with_questions_stream(
        self,
        project_id: str,
        count: int = 30,
        user_prompt: Optional[str] = None,
    ) -> AsyncGenerator[dict, None]:
        """Create a quiz with streaming progress updates.

        Args:
            project_id: The project ID
            count: Number of questions to generate
            user_prompt: Optional user instructions for generation

        Yields:
            Progress update dictionaries with status and message
        """
        try:
            yield {"status": "searching", "message": "Searching documents..."}

            with self._get_db_session() as db:
                # Get project language code
                project = db.query(Project).filter(Project.id == project_id).first()
                if not project:
                    yield {
                        "status": "done",
                        "message": "Error: Project not found",
                        "error": f"Project {project_id} not found",
                    }
                    return

                language_code = project.language_code

                # Extract topic from user_prompt if provided
                topic = None
                if user_prompt:
                    topic = user_prompt

                yield {"status": "analyzing", "message": "Analyzing content..."}

                # Get project documents content
                document_content = await self._get_project_documents_content(
                    project_id, topic=topic
                )
                if not document_content:
                    if topic:
                        error_msg = f"No documents found related to '{topic}'. Please upload relevant documents or try a different topic."
                    else:
                        error_msg = "No documents found in project. Please upload documents first."
                    yield {
                        "status": "done",
                        "message": "Error: No documents found",
                        "error": error_msg,
                    }
                    return

                yield {
                    "status": "generating",
                    "message": f"Generating {count} questions...",
                }

                # Generate content
                generated_content = await self._generate_quiz_content(
                    db=db,
                    project_id=project_id,
                    count=count,
                    user_prompt=user_prompt,
                )

                name = generated_content.name
                description = generated_content.description
                questions_data = generated_content.questions

                # Create quiz in database
                quiz = Quiz(
                    id=str(uuid.uuid4()),
                    project_id=project_id,
                    name=name,
                    description=description,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
                db.add(quiz)
                db.flush()  # Flush to get quiz.id

                # Save questions to database
                for question_item in questions_data:
                    question = QuizQuestion(
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
                    db.add(question)

                db.commit()

                logger.info(f"generated {len(questions_data)} quiz questions")

                yield {
                    "status": "done",
                    "message": "Quiz created successfully",
                    "quiz_id": str(quiz.id),
                }

        except ValueError as e:
            logger.error(f"error creating quiz: {e}")
            yield {
                "status": "done",
                "message": "Error creating quiz",
                "error": str(e),
            }
        except Exception as e:
            logger.error(f"error creating quiz: {e}", exc_info=True)
            yield {
                "status": "done",
                "message": "Error creating quiz",
                "error": "Failed to create quiz. Please try again.",
            }

    def get_quizzes(self, project_id: str) -> List[Quiz]:
        """Get all quizzes for a project.

        Args:
            project_id: The project ID

        Returns:
            List of Quiz model instances
        """
        with self._get_db_session() as db:
            try:
                logger.info(f"getting quizzes for project_id={project_id}")

                quizzes = (
                    db.query(Quiz)
                    .filter(Quiz.project_id == project_id)
                    .order_by(Quiz.created_at.desc())
                    .all()
                )

                logger.info(f"found {len(quizzes)} quizzes")
                return quizzes
            except Exception as e:
                logger.error(f"error getting quizzes for project_id={project_id}: {e}")
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
                logger.info(f"getting quiz questions for quiz_id={quiz_id}")

                questions = (
                    db.query(QuizQuestion)
                    .filter(QuizQuestion.quiz_id == quiz_id)
                    .order_by(QuizQuestion.position.asc())
                    .all()
                )

                logger.info(f"found {len(questions)} quiz questions")
                return questions
            except Exception as e:
                logger.error(f"error getting quiz questions for quiz_id={quiz_id}: {e}")
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
        explanation: Optional[str] = None,
        difficulty_level: str = "medium",
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
            correct_option: Correct option (a, b, c, or d)
            explanation: Optional explanation
            difficulty_level: Difficulty level (easy, medium, hard)
            position: Optional position for ordering. If None, appends to end.

        Returns:
            Created QuizQuestion model instance

        Raises:
            ValueError: If quiz not found
        """
        with self._get_db_session() as db:
            try:
                logger.info(f"creating quiz question for quiz_id={quiz_id}")

                # Verify quiz exists
                quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
                if not quiz:
                    raise ValueError(f"Quiz {quiz_id} not found")

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
                    correct_option=correct_option,
                    explanation=explanation,
                    difficulty_level=difficulty_level,
                    position=position,
                    created_at=datetime.now(),
                )

                db.add(question)
                db.commit()
                db.refresh(question)

                logger.info(f"created quiz question_id={question.id}")
                return question
            except ValueError:
                raise
            except Exception as e:
                logger.error(f"error creating quiz question for quiz_id={quiz_id}: {e}")
                raise

    def update_quiz_question(
        self,
        question_id: str,
        question_text: Optional[str] = None,
        option_a: Optional[str] = None,
        option_b: Optional[str] = None,
        option_c: Optional[str] = None,
        option_d: Optional[str] = None,
        correct_option: Optional[str] = None,
        explanation: Optional[str] = None,
        difficulty_level: Optional[str] = None,
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
                logger.info(f"updating quiz question_id={question_id}")

                question = (
                    db.query(QuizQuestion)
                    .filter(QuizQuestion.id == question_id)
                    .first()
                )
                if not question:
                    logger.warning(f"quiz question_id={question_id} not found")
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
                    question.correct_option = correct_option
                if explanation is not None:
                    question.explanation = explanation
                if difficulty_level is not None:
                    question.difficulty_level = difficulty_level

                db.commit()
                db.refresh(question)

                logger.info(f"updated quiz question_id={question_id}")
                return question
            except Exception as e:
                logger.error(
                    f"error updating quiz question question_id={question_id}: {e}"
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
                logger.info(
                    f"reordering quiz questions for quiz_id={quiz_id}, count={len(question_ids)}"
                )

                # Verify quiz exists
                quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
                if not quiz:
                    raise ValueError(f"Quiz {quiz_id} not found")

                # Get all questions in the quiz
                questions = (
                    db.query(QuizQuestion).filter(QuizQuestion.quiz_id == quiz_id).all()
                )
                question_dict = {q.id: q for q in questions}

                # Verify all provided IDs exist and belong to the quiz
                for question_id in question_ids:
                    if question_id not in question_dict:
                        raise ValueError(
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

                logger.info(f"reordered {len(updated_questions)} quiz questions")
                return updated_questions
            except ValueError:
                raise
            except Exception as e:
                logger.error(
                    f"error reordering quiz questions for quiz_id={quiz_id}: {e}"
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
                logger.info(f"deleting quiz question_id={question_id}")

                question = (
                    db.query(QuizQuestion)
                    .filter(QuizQuestion.id == question_id)
                    .first()
                )

                if not question:
                    logger.warning(f"quiz question_id={question_id} not found")
                    return False

                db.delete(question)
                db.commit()

                logger.info(f"deleted quiz question_id={question_id}")
                return True
            except Exception as e:
                logger.error(
                    f"error deleting quiz question question_id={question_id}: {e}"
                )
                raise

    def get_quiz(self, quiz_id: str) -> Quiz:
        """Get a specific quiz by ID.

        Args:
            quiz_id: The quiz ID

        Returns:
            Quiz model instance

        Raises:
            ValueError: If quiz not found
        """
        with self._get_db_session() as db:
            try:
                logger.info(f"getting quiz_id={quiz_id}")

                quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
                if not quiz:
                    raise ValueError(f"Quiz {quiz_id} not found")

                logger.info(f"found quiz_id={quiz_id}")
                return quiz
            except ValueError:
                raise
            except Exception as e:
                logger.error(f"error getting quiz quiz_id={quiz_id}: {e}")
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
            ValueError: If quiz not found
        """
        with self._get_db_session() as db:
            try:
                logger.info(f"updating quiz_id={quiz_id}")

                quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
                if not quiz:
                    raise ValueError(f"Quiz {quiz_id} not found")

                if name is not None:
                    quiz.name = name
                if description is not None:
                    quiz.description = description
                quiz.updated_at = datetime.now()
                db.commit()
                db.refresh(quiz)

                logger.info(f"updated quiz_id={quiz_id}")
                return quiz
            except ValueError:
                raise
            except Exception as e:
                logger.error(f"error updating quiz quiz_id={quiz_id}: {e}")
                raise

    def delete_quiz(self, quiz_id: str) -> bool:
        """Delete a quiz and all its questions.

        Args:
            quiz_id: The quiz ID

        Returns:
            True if deleted successfully

        Raises:
            ValueError: If quiz not found
        """
        with self._get_db_session() as db:
            try:
                logger.info(f"deleting quiz_id={quiz_id}")

                quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
                if not quiz:
                    raise ValueError(f"Quiz {quiz_id} not found")

                # Delete all questions in the quiz first (cascade should handle this)
                db.delete(quiz)
                db.commit()

                logger.info(f"deleted quiz_id={quiz_id}")
                return True
            except ValueError:
                raise
            except Exception as e:
                logger.error(f"error deleting quiz quiz_id={quiz_id}: {e}")
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
                logger.info(f"submitting answers for quiz_id={quiz_id}")

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

                logger.info(
                    f"quiz_id={quiz_id} completed: correct_answers={correct_answers}/{total_questions} (score_percentage={score_percentage:.1f}%)"
                )
                return quiz_result
            except ValueError:
                raise
            except Exception as e:
                logger.error(
                    f"error submitting quiz answers for quiz_id={quiz_id}: {e}"
                )
                raise

    async def _generate_quiz_content(
        self,
        db: Session,
        project_id: str,
        count: int = 30,
        user_prompt: Optional[str] = None,
    ) -> QuizGenerationResult:
        """Generate quiz name, description, and questions in one call.

        Args:
            db: Database session
            project_id: The project ID
            count: Number of questions to generate
            user_prompt: Optional user instructions

        Returns:
            QuizGenerationResult containing name, description, and questions

        Raises:
            ValueError: If project not found or no documents available
        """
        try:
            logger.info(f"generating quiz content for project_id={project_id}")

            # Get project language code
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                raise ValueError(f"Project {project_id} not found")

            language_code = project.language_code

            # Extract topic from user_prompt if provided
            # If user_prompt contains topic-like instructions, use it for filtering
            topic = None
            if user_prompt:
                # Use user_prompt as topic for document search
                # This allows topic-based filtering
                topic = user_prompt

            # Get project documents content, optionally filtered by topic
            document_content = await self._get_project_documents_content(
                project_id, topic=topic
            )
            if not document_content:
                if topic:
                    raise ValueError(
                        f"No documents found related to '{topic}'. Please upload relevant documents or try a different topic."
                    )
                raise ValueError(
                    "No documents found in project. Please upload documents first."
                )

            logger.info(
                f"found {len(document_content)} chars of content in project_id={project_id}"
            )

            # Create prompt template
            prompt_template = self._create_quiz_prompt_template()

            # Build the prompt
            prompt = prompt_template.format(
                document_content=document_content[
                    :8000
                ],  # Limit content to avoid token limits
                count=count,
                user_prompt=user_prompt
                or "Generate comprehensive quiz questions covering key concepts, definitions, and important details.",
                language_code=language_code,
                format_instructions=self.quiz_parser.get_format_instructions(),
            )

            # Generate content
            response = await self.llm.ainvoke(prompt)

            # Parse the response - JsonOutputParser returns dict, convert to QuizGenerationRequest
            parsed_dict = self.quiz_parser.parse(response.content)
            generation_request = QuizGenerationRequest(**parsed_dict)

            return QuizGenerationResult(
                name=generation_request.name,
                description=generation_request.description,
                questions=generation_request.questions,
            )
        except ValueError:
            raise
        except Exception as e:
            logger.error(
                f"error generating quiz content for project_id={project_id}: {e}"
            )
            raise

    async def _get_project_documents_content(
        self, project_id: str, topic: Optional[str] = None
    ) -> str:
        """Get document content for a project, optionally filtered by topic.

        Args:
            project_id: The project ID
            topic: Optional topic to filter documents by

        Returns:
            Combined document content as string
        """
        try:
            # If topic is provided, search for relevant documents
            # Otherwise, get all content
            query = topic if topic else ""
            top_k = 50 if topic else 100  # Fewer results when filtering by topic

            search_results = await self.search_interface.search_documents(
                query=query,
                project_id=project_id,
                top_k=top_k,
            )

            if not search_results:
                return ""

            # Combine all content
            content_parts = []
            for result in search_results:
                content_parts.append(result.content)

            return "\n\n".join(content_parts)
        except Exception as e:
            logger.error(
                f"error getting project documents content for project_id={project_id}: {e}"
            )
            return ""

    def _create_quiz_prompt_template(self) -> PromptTemplate:
        """Create the prompt template for quiz generation.

        Returns:
            PromptTemplate instance
        """
        template = """You are an expert educational content creator specializing in assessment design. Your goal is to create quizzes that accurately measure student understanding and promote learning through well-designed questions and explanations.

Document Content:
{document_content}

User Instructions: {user_prompt}

CRITICAL LANGUAGE REQUIREMENT: You MUST generate ALL content in {language_code} language. This includes:
- Quiz name and description
- All questions
- All answer options (A, B, C, D)
- All explanations
Never use any language other than {language_code}. If the document content is in a different language, translate all relevant information to {language_code}.

Educational Guidelines for quiz creation:
1. Name: Generate a concise, descriptive name (2-6 words) in {language_code} that captures the main topic or theme being assessed
2. Description: Generate a clear description (1-2 sentences) in {language_code} explaining what knowledge and skills the quiz will evaluate
3. Learning-focused questions: Create questions that test understanding, application, analysis, and synthesis - not just factual recall
4. Difficulty distribution: Include a balanced mix of difficulty levels:
   - Easy: Basic recall and understanding of key concepts
   - Medium: Application of concepts to new situations
   - Hard: Analysis, evaluation, and synthesis requiring deep understanding
5. Comprehensive coverage: Cover key concepts, definitions, important facts, relationships between ideas, and practical applications
6. Question clarity: Make questions clear, unambiguous, and focused on a single concept or skill
7. Answer options: Provide exactly 4 plausible options (A, B, C, D) with only one clearly correct answer
8. Distractor quality: Make incorrect options (distractors) plausible enough to test real understanding, but clearly wrong to students who have mastered the material
9. Explanations: Provide detailed, educational explanations for the correct answer that help students understand:
   - Why the correct answer is right
   - Why the incorrect options are wrong
   - The underlying concept or principle
   - How to approach similar questions in the future
10. Educational value: Focus on the most pedagogically important content that will help students assess and improve their understanding
11. Fair assessment: Ensure questions are fair, test actual knowledge from the documents, and align with the learning objectives
12. Progressive difficulty: Structure questions to progress from foundational to more complex concepts when appropriate

{format_instructions}

Generate exactly {count} high-quality quiz questions in {language_code} that are relevant to the document content, follow the user's instructions, and effectively assess student understanding."""

        return PromptTemplate(
            template=template,
            input_variables=[
                "document_content",
                "count",
                "user_prompt",
                "language_code",
                "format_instructions",
            ],
        )

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
