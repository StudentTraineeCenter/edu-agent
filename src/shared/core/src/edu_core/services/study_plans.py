from datetime import datetime
from uuid import uuid4
from contextlib import contextmanager

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from edu_db.models import Flashcard, PracticeRecord, Project, Quiz, StudyPlan
from edu_db.session import get_session_factory
from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import AzureChatOpenAI

from edu_core.exceptions import NotFoundError
from edu_core.schemas.study_plans import StudyPlanDto
from edu_core.services.practice import (
    PracticeService,  # Reusing practice service if needed, or querying directly
)
from edu_ai.agents.utils import generate


class StudyPlanService:
    """Service for managing personalized study plans."""

    def __init__(
        self,
        azure_openai_chat_deployment: str | None = None,
        azure_openai_endpoint: str | None = None,
        azure_openai_api_version: str | None = None,
        azure_ad_token_provider=None,
    ) -> None:
        """Initialize the study plan service.

        Args:
            azure_openai_chat_deployment: Azure OpenAI chat deployment name
            azure_openai_endpoint: Azure OpenAI endpoint URL
            azure_openai_api_version: Azure OpenAI API version
            azure_ad_token_provider: Token provider for Azure AD auth
        """
        self.llm = None
        if azure_openai_chat_deployment and azure_openai_endpoint:
            # Initialize token provider if not passed
            token_provider = azure_ad_token_provider
            if not token_provider:
                credential = DefaultAzureCredential()
                token_provider = get_bearer_token_provider(
                    credential, "https://cognitiveservices.azure.com/.default"
                )

            # Build LLM kwargs
            llm_kwargs = {
                "azure_deployment": azure_openai_chat_deployment,
                "azure_endpoint": azure_openai_endpoint,
                "temperature": 0.7,
                "azure_ad_token_provider": token_provider,
            }
            if azure_openai_api_version:
                llm_kwargs["api_version"] = azure_openai_api_version

            self.llm = AzureChatOpenAI(**llm_kwargs)

    def get_latest_study_plan(self, user_id: str, project_id: str) -> StudyPlanDto | None:
        """Get the latest study plan for a user in a project.

        Args:
            user_id: The user ID
            project_id: The project ID

        Returns:
            Latest StudyPlanDto or None if no plan exists
        """
        with self._get_db_session() as db:
            plan = (
                db.query(StudyPlan)
                .filter(StudyPlan.user_id == user_id, StudyPlan.project_id == project_id)
                .order_by(StudyPlan.created_at.desc())
                .first()
            )
            
            if not plan:
                return None
            
            return self._model_to_dto(plan)
            
    def list_study_plans(self, user_id: str, project_id: str) -> list[StudyPlanDto]:
        """List all study plans for a user in a project.

        Args:
            user_id: The user ID
            project_id: The project ID

        Returns:
            List of StudyPlanDto
        """
        with self._get_db_session() as db:
            plans = (
                db.query(StudyPlan)
                .filter(StudyPlan.user_id == user_id, StudyPlan.project_id == project_id)
                .order_by(StudyPlan.created_at.desc())
                .all()
            )
            return [self._model_to_dto(p) for p in plans]

    async def generate_study_plan(self, user_id: str, project_id: str) -> StudyPlanDto:
        """Generate a new study plan based on user performance.

        Args:
            user_id: The user ID
            project_id: The project ID
        
        Returns:
            Created StudyPlanDto
        """
        if not self.llm:
            raise ValueError("Azure OpenAI not configured for generating study plans.")

        with self._get_db_session() as db:
            # 1. Fetch Practice Records
            records = (
                db.query(PracticeRecord)
                .filter(PracticeRecord.user_id == user_id, PracticeRecord.project_id == project_id)
                .all()
            )
            
            if not records:
                 # No practice history, generate a generic plan? Or raise?
                 # Let's generate a "Getting Started" plan.
                 weak_topics = []
                 performance_summary = "No practice history available yet."
            else:
                # 2. Analyze Weak Topics
                topic_stats = {}
                for record in records:
                    topic = record.topic or "General"
                    if topic not in topic_stats:
                        topic_stats[topic] = {"correct": 0, "total": 0}
                    topic_stats[topic]["total"] += 1
                    if record.was_correct:
                        topic_stats[topic]["correct"] += 1
                
                weak_topics = []
                performance_lines = []
                for topic, stats in topic_stats.items():
                    success_rate = (stats["correct"] / stats["total"]) * 100
                    performance_lines.append(f"- {topic}: {success_rate:.1f}% ({stats['correct']}/{stats['total']})")
                    if success_rate < 70:
                        weak_topics.append(topic)
                
                performance_summary = "\\n".join(performance_lines)

            # 3. Get Available Resources (Quizzes and Flashcards) to recommend
            # Only fetch names/ids to keep context small

            project = db.query(Project).filter(Project.id == project_id).first()
            language_code = project.language_code if project else "en"

            quizzes = db.query(Quiz).filter(Quiz.project_id == project_id).all()
            flashcards = db.query(Flashcard).filter(Flashcard.project_id == project_id).all()
            
            resources_summary = "Available Resources:\\n"
            resources_summary += "Quizzes:\\n" + "\\n".join([f"- {q.name} (ID: {q.id}, Parent ID: {q.id})" for q in quizzes])
            resources_summary += "\\nFlashcards:\\n" + "\\n".join([f"- {f.question[:50]}... (ID: {f.id}, Parent ID: {f.group_id})" for f in flashcards[:20]]) # Limit flashcards
            
            # 4. Use generate utility
            from edu_core.schemas.study_plan_generation import StudyPlanContent
            
            document_content = f"""
            Student Performance:
            {performance_summary}
            
            Weak Topics Identified (Success Rate < 70%):
            {weak_topics}
            
            {resources_summary}
            """

            # Template expecting {document_content} which is passed by the utility as context_text
            prompt_template = "study_plan"

            plan_data = await generate(
                llm=self.llm,
                search_service=None, # Not used since we provide document_content
                output_model=StudyPlanContent,
                prompt_template=prompt_template,
                project_id=project_id,
                topic="Study Plan",
                language_code=language_code,
                document_content=document_content
            )
            
            # 5. Save Study Plan
            study_plan = StudyPlan(
                id=str(uuid4()),
                user_id=user_id,
                project_id=project_id,
                content=plan_data.model_dump(),  # Save as JSON
                weak_topics=weak_topics,
                created_at=datetime.now()
            )
            
            db.add(study_plan)
            db.commit()
            db.refresh(study_plan)
            
            return self._model_to_dto(study_plan)

    def _model_to_dto(self, plan: StudyPlan) -> StudyPlanDto:
        """Convert StudyPlan model to DTO."""
        # Ensure content is a dict/object for the DTO
        content = plan.content
        # If for some reason it's still a string (old records), we might want to handle it, 
        # but for now assume schema migration handles it or new records only.
        # Actually sqlalchemy JSON type returns python dicts.
        
        return StudyPlanDto(
            id=plan.id,
            user_id=plan.user_id,
            project_id=plan.project_id,
            content=content, 
            weak_topics=plan.weak_topics,
            created_at=plan.created_at,
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
