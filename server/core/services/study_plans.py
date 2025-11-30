"""Service for managing study plans with AI generation capabilities."""

import uuid
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import AzureChatOpenAI
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from core.config import app_config
from core.logger import get_logger
from core.services.attempts import AttemptService
from db.models import FlashcardGroup, Project, Quiz, StudyAttempt, StudyPlan
from db.session import SessionLocal

logger = get_logger(__name__)


class StudyPlanGenerationRequest(BaseModel):
    """Pydantic model for study plan generation request."""

    title: str = Field(description="Title of the study plan")
    description: str = Field(description="Description of the study plan")
    weak_topics: List[Dict[str, Any]] = Field(
        description="List of topics with low accuracy that need more practice"
    )
    strong_topics: List[Dict[str, Any]] = Field(
        description="List of topics with high accuracy"
    )
    study_schedule: List[Dict[str, Any]] = Field(
        description="Daily study schedule with recommended activities"
    )
    overall_performance: Dict[str, Any] = Field(
        description="Overall performance statistics"
    )


class StudyPlanService:
    """Service for managing study plans with AI generation capabilities."""

    def __init__(self, attempt_service: AttemptService) -> None:
        """Initialize the study plan service.

        Args:
            attempt_service: Service for accessing study attempts
        """
        self.attempt_service = attempt_service
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

        self.plan_parser = JsonOutputParser(pydantic_object=StudyPlanGenerationRequest)

    async def generate_study_plan(
        self, user_id: str, project_id: str
    ) -> StudyPlan:
        """Generate personalized study plan based on study attempts.

        Args:
            user_id: The user's unique identifier
            project_id: The project ID

        Returns:
            Created or updated StudyPlan model instance

        Raises:
            ValueError: If no study attempts found
        """
        with self._get_db_session() as db:
            try:
                logger.info(
                    f"generating study plan for user_id={user_id}, project_id={project_id}"
                )

                # Get project for language code
                project = db.query(Project).filter(Project.id == project_id).first()
                if not project:
                    raise ValueError(f"Project {project_id} not found")

                # Get all attempts for this project
                attempts = self.attempt_service.get_user_attempts(
                    user_id=user_id, project_id=project_id
                )

                if not attempts:
                    raise ValueError(
                        "No study attempts found. Complete some quizzes or flashcards first."
                    )

                # Analyze attempts by topic
                topic_analysis = self._analyze_attempts_by_topic(attempts)

                # Get available study resources
                available_resources = self._get_available_resources(db, project_id)

                # Generate plan using AI
                plan_content = await self._generate_plan_with_ai(
                    topic_analysis=topic_analysis,
                    available_resources=available_resources,
                    project_language=project.language_code,
                )

                # Check if plan already exists (1 plan per project)
                existing_plan = (
                    db.query(StudyPlan)
                    .filter(StudyPlan.project_id == project_id)
                    .first()
                )

                if existing_plan:
                    # Update existing plan
                    existing_plan.title = plan_content.title
                    existing_plan.description = plan_content.description
                    existing_plan.plan_content = plan_content.model_dump()
                    existing_plan.updated_at = datetime.now()
                    db.commit()
                    db.refresh(existing_plan)
                    logger.info(f"updated study plan id={existing_plan.id}")
                    return existing_plan
                else:
                    # Create new plan
                    plan = StudyPlan(
                        id=str(uuid.uuid4()),
                        user_id=user_id,
                        project_id=project_id,
                        title=plan_content.title,
                        description=plan_content.description,
                        plan_content=plan_content.model_dump(),
                        generated_at=datetime.now(),
                        updated_at=datetime.now(),
                    )
                    db.add(plan)
                    db.commit()
                    db.refresh(plan)
                    logger.info(f"created study plan id={plan.id}")
                    return plan

            except ValueError:
                raise
            except Exception as e:
                logger.error(
                    f"error generating study plan for user_id={user_id}, project_id={project_id}: {e}"
                )
                raise

    def get_latest_plan(
        self, user_id: str, project_id: str
    ) -> Optional[StudyPlan]:
        """Get the latest study plan for a project.

        Args:
            user_id: The user's unique identifier
            project_id: The project ID

        Returns:
            StudyPlan model instance or None if not found
        """
        with self._get_db_session() as db:
            try:
                plan = (
                    db.query(StudyPlan)
                    .filter(
                        StudyPlan.user_id == user_id,
                        StudyPlan.project_id == project_id,
                    )
                    .first()
                )

                if plan:
                    logger.info(
                        f"retrieved study plan id={plan.id} for user_id={user_id}, project_id={project_id}"
                    )
                else:
                    logger.info(
                        f"no study plan found for user_id={user_id}, project_id={project_id}"
                    )

                return plan
            except Exception as e:
                logger.error(
                    f"error retrieving study plan for user_id={user_id}, project_id={project_id}: {e}"
                )
                raise

    def _analyze_attempts_by_topic(
        self, attempts: List[StudyAttempt]
    ) -> Dict[str, Dict[str, Any]]:
        """Analyze attempts grouped by topic.

        Args:
            attempts: List of study attempts

        Returns:
            Dictionary mapping topics to their statistics
        """
        topic_stats: Dict[str, Dict[str, Any]] = {}

        for attempt in attempts:
            topic = attempt.topic
            if topic not in topic_stats:
                topic_stats[topic] = {
                    "total": 0,
                    "correct": 0,
                    "attempts": [],
                }

            topic_stats[topic]["total"] += 1
            if attempt.was_correct:
                topic_stats[topic]["correct"] += 1
            topic_stats[topic]["attempts"].append(attempt)

        # Calculate accuracy for each topic
        for topic, stats in topic_stats.items():
            stats["accuracy"] = (
                (stats["correct"] / stats["total"]) * 100 if stats["total"] > 0 else 0
            )

        return topic_stats

    def _get_available_resources(
        self, db: Session, project_id: str
    ) -> Dict[str, List[Dict[str, str]]]:
        """Get available study resources (flashcards and quizzes) for the project.

        Args:
            db: Database session
            project_id: The project ID

        Returns:
            Dictionary with available resources
        """
        flashcards = (
            db.query(FlashcardGroup)
            .filter(FlashcardGroup.project_id == project_id)
            .all()
        )
        quizzes = db.query(Quiz).filter(Quiz.project_id == project_id).all()

        return {
            "flashcards": [
                {"id": fg.id, "name": fg.name, "description": fg.description or ""}
                for fg in flashcards
            ],
            "quizzes": [
                {"id": q.id, "name": q.name, "description": q.description or ""}
                for q in quizzes
            ],
        }

    async def _generate_plan_with_ai(
        self,
        topic_analysis: Dict[str, Dict[str, Any]],
        available_resources: Dict[str, List[Dict[str, str]]],
        project_language: str,
    ) -> StudyPlanGenerationRequest:
        """Use AI to generate personalized study plan.

        Args:
            topic_analysis: Analysis of attempts by topic
            available_resources: Available flashcards and quizzes
            project_language: Language code for the project

        Returns:
            StudyPlanGenerationRequest with generated plan
        """
        try:
            logger.info("generating study plan with AI")

            # Separate weak and strong topics
            weak_topics = []
            strong_topics = []
            total_attempts = 0
            total_correct = 0

            for topic, stats in topic_analysis.items():
                accuracy = stats["accuracy"]
                total_attempts += stats["total"]
                total_correct += stats["correct"]

                topic_data = {
                    "topic": topic,
                    "accuracy": round(accuracy, 1),
                    "attempts_count": stats["total"],
                    "correct_count": stats["correct"],
                }

                if accuracy < 70:  # Weak topic threshold
                    weak_topics.append(topic_data)
                else:
                    strong_topics.append(topic_data)

            overall_accuracy = (
                (total_correct / total_attempts) * 100 if total_attempts > 0 else 0
            )

            # Build prompt
            prompt_template = self._create_plan_prompt_template()
            prompt = prompt_template.format(
                weak_topics=str(weak_topics),
                strong_topics=str(strong_topics),
                available_flashcards=str(available_resources["flashcards"]),
                available_quizzes=str(available_resources["quizzes"]),
                overall_accuracy=round(overall_accuracy, 1),
                total_attempts=total_attempts,
                language_code=project_language,
                format_instructions=self.plan_parser.get_format_instructions(),
            )

            # Generate content
            response = await self.llm.ainvoke(prompt)

            # Parse the response
            parsed_dict = self.plan_parser.parse(response.content)
            generation_request = StudyPlanGenerationRequest(**parsed_dict)

            return generation_request
        except Exception as e:
            logger.error(f"error generating plan with AI: {e}")
            raise

    def _create_plan_prompt_template(self) -> PromptTemplate:
        """Create the prompt template for study plan generation.

        Returns:
            PromptTemplate instance
        """
        template = """You are an expert educational AI tutor specializing in creating personalized study plans. Your goal is to help students improve their learning by analyzing their performance and creating a structured, actionable study plan.

Performance Analysis:
Weak Topics (need more practice): {weak_topics}
Strong Topics (good performance): {strong_topics}

Available Study Resources:
Flashcards: {available_flashcards}
Quizzes: {available_quizzes}

Overall Performance:
- Total Attempts: {total_attempts}
- Overall Accuracy: {overall_accuracy}%

CRITICAL LANGUAGE REQUIREMENT: You MUST generate ALL content in {language_code} language. This includes:
- Plan title and description
- All topic names and recommendations
- All activity descriptions
- All text in the study schedule
Never use any language other than {language_code}.

Guidelines for study plan creation:
1. Title: Generate a concise, motivating title (3-8 words) in {language_code} that reflects the personalized nature of the plan
2. Description: Generate a clear description (2-3 sentences) in {language_code} explaining what the plan covers and its purpose
3. Weak Topics: For each weak topic, provide:
   - The topic name (as provided)
   - Accuracy percentage (as provided)
   - Specific recommendations (2-3 actionable items) referencing available flashcards/quizzes by name
   - Suggested study activities
4. Strong Topics: List topics where the student performs well (for positive reinforcement)
5. Study Schedule: Create a 7-day study schedule with:
   - Day number (1-7)
   - Focus topic(s) for that day
   - Specific activities (e.g., "Review flashcards: [name]", "Take quiz: [name]")
   - Estimated time (e.g., "30 min", "45 min")
   - Mix of weak topics and review of strong topics
6. Overall Performance: Include summary statistics and trend analysis
7. Prioritization: Focus on weak topics but include review of strong topics to maintain knowledge
8. Realistic Planning: Ensure daily study time is reasonable (30-60 minutes per day)
9. Progressive Difficulty: Start with easier topics and gradually move to more challenging ones
10. Variety: Mix different types of activities (flashcards, quizzes, review)

{format_instructions}

Generate a comprehensive, personalized study plan in {language_code} that helps the student improve their weak areas while maintaining their strengths."""

        return PromptTemplate(
            template=template,
            input_variables=[
                "weak_topics",
                "strong_topics",
                "available_flashcards",
                "available_quizzes",
                "overall_accuracy",
                "total_attempts",
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

