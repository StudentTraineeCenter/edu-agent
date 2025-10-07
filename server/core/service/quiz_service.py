import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from contextlib import contextmanager

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from langchain_openai import AzureChatOpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

from core.logger import get_logger
from core.config import app_config
from db.model import Quiz, QuizQuestion, Project
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


class QuizService:
    """Service for managing quizzes with AI generation capabilities."""

    def __init__(self):
        """Initialize the quiz service."""
        self._setup_langchain_components()
        self._setup_document_service()

    def _setup_langchain_components(self) -> None:
        """Initialize LangChain components for quiz generation."""
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

    def _setup_document_service(self) -> None:
        """Initialize document service for content retrieval."""
        from core.service.document_service import DocumentService

        self.document_service = DocumentService()

    async def _get_project_documents_content(self, project_id: str) -> str:
        """Get all document content for a project."""
        try:
            # Search for all content in the project
            search_results = await self.document_service.search_documents(
                query="",  # Empty query to get all content
                project_id=project_id,
                top_k=100,  # Get more content for better generation
            )

            if not search_results:
                return ""

            # Combine all content
            content_parts = []
            for result in search_results:
                content_parts.append(result["content"])

            return "\n\n".join(content_parts)

        except Exception as e:
            logger.error(f"Error getting project documents content: {e}")
            return ""

    def _get_project_language_code(self, project_id: str) -> str:
        """Get the language code for a project."""
        with self._get_db_session() as db:
            project = db.query(Project).filter(Project.id == project_id).first()
            return project.language_code if project else "en"

    def _create_quiz_prompt_template(self) -> PromptTemplate:
        """Create the prompt template for quiz generation."""
        template = """You are an expert educational content creator. Based on the following document content, generate a quiz with name, description, and {count} high-quality multiple-choice questions.

Document Content:
{document_content}

User Instructions: {user_prompt}

IMPORTANT: Generate all content in {language_code} language. All names, descriptions, questions, options, and explanations must be in {language_code}.

Guidelines for quiz creation:
1. Generate a concise name (2-6 words) that captures the main topic or theme
2. Generate a description (1-2 sentences) explaining what the quiz will test
3. Create questions that test understanding, not just memorization
4. Include a mix of difficulty levels (easy, medium, hard)
5. Cover key concepts, definitions, important facts, and practical applications
6. Make questions clear and concise
7. Provide 4 plausible options (A, B, C, D) with only one correct answer
8. Make incorrect options plausible but clearly wrong to someone who understands the material
9. Provide detailed explanations for the correct answer
10. Focus on the most important and educational content from the documents
11. Ensure questions are fair and test actual knowledge from the documents

{format_instructions}

Generate exactly {count} quiz questions that are relevant to the document content and follow the user's instructions."""

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

    async def create_quiz_with_questions(
        self,
        project_id: str,
        count: int = 30,
        user_prompt: Optional[str] = None,
    ) -> Quiz:
        """Create a new quiz with auto-generated name, description, and questions."""
        try:
            logger.info(
                f"Creating quiz with {count} questions for project {project_id}"
            )

            # Generate all content using LangChain directly
            generated_content = await self._generate_quiz_content(
                project_id=project_id,
                count=count,
                user_prompt=user_prompt,
            )

            name = generated_content["name"]
            description = generated_content["description"]
            questions_data = generated_content["questions"]

            logger.info(f"Creating quiz '{name}' for project {project_id}")

            with self._get_db_session() as db:
                # Verify project exists
                project = db.query(Project).filter(Project.id == project_id).first()
                if not project:
                    raise ValueError(f"Project {project_id} not found")

                # Create quiz
                quiz = Quiz(
                    id=str(uuid.uuid4()),
                    project_id=project_id,
                    name=name,
                    description=description,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )

                db.add(quiz)
                db.commit()
                db.refresh(quiz)

                logger.info(f"Created quiz: {quiz.id}")

                # Save quiz questions to database
                question_ids = await self._save_quiz_questions_to_db(
                    quiz.id, project_id, questions_data
                )

                logger.info(f"Generated and saved {len(question_ids)} quiz questions")
                return quiz

        except Exception as e:
            logger.error(f"Error creating quiz with questions: {e}")
            raise

    async def _generate_quiz_content(
        self,
        project_id: str,
        count: int = 30,
        user_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate quiz name, description, and questions in one call."""
        try:
            logger.info(f"Generating quiz content for project {project_id}")

            # Get project language code
            language_code = self._get_project_language_code(project_id)
            logger.info(
                f"Using language code: {language_code} for project {project_id}"
            )

            # Get project documents content
            document_content = await self._get_project_documents_content(project_id)
            if not document_content:
                raise ValueError(
                    "No documents found in project. Please upload documents first."
                )

            logger.info(
                f"Found {len(document_content)} chars of content in project {project_id}"
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

            # Parse the response
            parsed_response = self.quiz_parser.parse(response.content)

            # Handle both dict and object responses
            if isinstance(parsed_response, dict):
                return {
                    "name": parsed_response.get("name", "Quiz"),
                    "description": parsed_response.get(
                        "description", "Auto-generated quiz"
                    ),
                    "questions": [
                        QuizQuestionData(**question_dict)
                        for question_dict in parsed_response.get("questions", [])
                    ],
                }
            else:
                return {
                    "name": parsed_response.name,
                    "description": parsed_response.description,
                    "questions": parsed_response.questions,
                }

        except Exception as e:
            logger.error(f"Error generating quiz content: {e}")
            raise

    async def _save_quiz_questions_to_db(
        self, quiz_id: str, project_id: str, questions_data: List[QuizQuestionData]
    ) -> List[str]:
        """Save generated quiz questions to the database."""
        try:
            question_ids = []

            with self._get_db_session() as db:
                for question_data in questions_data:
                    quiz_question = QuizQuestion(
                        id=str(uuid.uuid4()),
                        quiz_id=quiz_id,
                        project_id=project_id,
                        question_text=question_data.question_text,
                        option_a=question_data.option_a,
                        option_b=question_data.option_b,
                        option_c=question_data.option_c,
                        option_d=question_data.option_d,
                        correct_option=question_data.correct_option,
                        explanation=question_data.explanation,
                        difficulty_level=question_data.difficulty_level,
                        created_at=datetime.now(),
                    )

                    db.add(quiz_question)
                    question_ids.append(quiz_question.id)

                db.commit()

            logger.info(f"Saved {len(question_ids)} quiz questions to database")
            return question_ids

        except Exception as e:
            logger.error(f"Error saving quiz questions to database: {e}")
            raise

    def get_quizzes(self, project_id: str) -> List[Quiz]:
        """Get all quizzes for a project."""
        try:
            logger.info(f"Getting quizzes for project {project_id}")

            with self._get_db_session() as db:
                quizzes = (
                    db.query(Quiz)
                    .filter(Quiz.project_id == project_id)
                    .order_by(Quiz.created_at.desc())
                    .all()
                )

                logger.info(f"Found {len(quizzes)} quizzes")
                return quizzes

        except Exception as e:
            logger.error(f"Error getting quizzes: {e}")
            raise

    def get_quiz_questions(self, quiz_id: str) -> List[QuizQuestion]:
        """Get all questions in a quiz."""
        try:
            logger.info(f"Getting quiz questions for quiz {quiz_id}")

            with self._get_db_session() as db:
                questions = (
                    db.query(QuizQuestion)
                    .filter(QuizQuestion.quiz_id == quiz_id)
                    .order_by(QuizQuestion.created_at.asc())
                    .all()
                )

                logger.info(f"Found {len(questions)} quiz questions")
                return questions

        except Exception as e:
            logger.error(f"Error getting quiz questions: {e}")
            raise

    def get_quiz(self, quiz_id: str) -> Optional[Quiz]:
        """Get a specific quiz by ID."""
        try:
            logger.info(f"Getting quiz {quiz_id}")

            with self._get_db_session() as db:
                quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()

                if quiz:
                    logger.info(f"Found quiz: {quiz_id}")
                else:
                    logger.info(f"Quiz not found: {quiz_id}")

                return quiz

        except Exception as e:
            logger.error(f"Error getting quiz: {e}")
            raise

    def get_project_id_from_quiz(self, quiz_id: str) -> Optional[str]:
        """Get project_id from a quiz ID."""
        try:
            quiz = self.get_quiz(quiz_id)
            return quiz.project_id if quiz else None
        except Exception as e:
            logger.error(f"Error getting project_id from quiz: {e}")
            return None

    def get_quiz_question(self, question_id: str) -> Optional[QuizQuestion]:
        """Get a specific quiz question by ID."""
        try:
            logger.info(f"Getting quiz question {question_id}")

            with self._get_db_session() as db:
                question = (
                    db.query(QuizQuestion)
                    .filter(QuizQuestion.id == question_id)
                    .first()
                )

                if question:
                    logger.info(f"Found quiz question: {question_id}")
                else:
                    logger.info(f"Quiz question not found: {question_id}")

                return question

        except Exception as e:
            logger.error(f"Error getting quiz question: {e}")
            raise

    def update_quiz(
        self,
        quiz_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[Quiz]:
        """Update a quiz."""
        try:
            logger.info(f"Updating quiz {quiz_id}")

            with self._get_db_session() as db:
                quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()

                if not quiz:
                    logger.warning(f"Quiz not found: {quiz_id}")
                    return None

                if name is not None:
                    quiz.name = name
                if description is not None:
                    quiz.description = description

                quiz.updated_at = datetime.now()
                db.commit()
                db.refresh(quiz)

                logger.info(f"Updated quiz: {quiz_id}")
                return quiz

        except Exception as e:
            logger.error(f"Error updating quiz: {e}")
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
        """Update a quiz question."""
        try:
            logger.info(f"Updating quiz question {question_id}")

            with self._get_db_session() as db:
                question = (
                    db.query(QuizQuestion)
                    .filter(QuizQuestion.id == question_id)
                    .first()
                )

                if not question:
                    logger.warning(f"Quiz question not found: {question_id}")
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

                logger.info(f"Updated quiz question: {question_id}")
                return question

        except Exception as e:
            logger.error(f"Error updating quiz question: {e}")
            raise

    def delete_quiz_question(self, question_id: str) -> bool:
        """Delete a quiz question."""
        try:
            logger.info(f"Deleting quiz question {question_id}")

            with self._get_db_session() as db:
                question = (
                    db.query(QuizQuestion)
                    .filter(QuizQuestion.id == question_id)
                    .first()
                )

                if not question:
                    logger.warning(f"Quiz question not found: {question_id}")
                    return False

                db.delete(question)
                db.commit()

                logger.info(f"Deleted quiz question: {question_id}")
                return True

        except Exception as e:
            logger.error(f"Error deleting quiz question: {e}")
            raise

    def delete_quiz(self, quiz_id: str) -> bool:
        """Delete a quiz and all its questions."""
        try:
            logger.info(f"Deleting quiz {quiz_id}")

            with self._get_db_session() as db:
                quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()

                if not quiz:
                    logger.warning(f"Quiz not found: {quiz_id}")
                    return False

                # Delete all questions in the quiz first (cascade should handle this)
                db.delete(quiz)
                db.commit()

                logger.info(f"Deleted quiz: {quiz_id}")
                return True

        except Exception as e:
            logger.error(f"Error deleting quiz: {e}")
            raise

    async def submit_quiz_answers(
        self, quiz_id: str, answers: Dict[str, str]
    ) -> Dict[str, Any]:
        """Submit quiz answers and get results."""
        try:
            logger.info(f"Submitting answers for quiz {quiz_id}")

            with self._get_db_session() as db:
                # Get all questions for the quiz
                questions = (
                    db.query(QuizQuestion).filter(QuizQuestion.quiz_id == quiz_id).all()
                )

                if not questions:
                    raise ValueError(f"No questions found for quiz {quiz_id}")

                # Calculate results
                total_questions = len(questions)
                correct_answers = 0
                results = []

                for question in questions:
                    user_answer = answers.get(question.id, "")
                    is_correct = user_answer.lower() == question.correct_option.lower()

                    if is_correct:
                        correct_answers += 1

                    results.append(
                        {
                            "question_id": question.id,
                            "question_text": question.question_text,
                            "user_answer": user_answer,
                            "correct_answer": question.correct_option,
                            "is_correct": is_correct,
                            "explanation": question.explanation,
                            "difficulty_level": question.difficulty_level,
                        }
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

                quiz_result = {
                    "quiz_id": quiz_id,
                    "total_questions": total_questions,
                    "correct_answers": correct_answers,
                    "score_percentage": round(score_percentage, 2),
                    "grade": grade,
                    "results": results,
                    "submitted_at": datetime.now().isoformat(),
                }

                logger.info(
                    f"Quiz {quiz_id} completed: {correct_answers}/{total_questions} correct ({score_percentage:.1f}%)"
                )
                return quiz_result

        except Exception as e:
            logger.error(f"Error submitting quiz answers: {e}")
            raise
