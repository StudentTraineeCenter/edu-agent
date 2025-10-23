import uuid
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from core.agents.search import SearchInterface
from core.config import app_config
from core.logger import get_logger
from db.models import Flashcard, FlashcardGroup, Project
from db.session import SessionLocal
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import AzureChatOpenAI
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

logger = get_logger(__name__)


class FlashcardData(BaseModel):
    """Pydantic model for flashcard data structure."""

    question: str = Field(description="The flashcard question")
    answer: str = Field(description="The flashcard answer")
    difficulty_level: str = Field(description="Difficulty level: easy, medium, or hard")


class FlashcardGroupGenerationRequest(BaseModel):
    """Pydantic model for flashcard group generation request."""

    name: str = Field(description="Generated name for the flashcard group")
    description: str = Field(
        description="Generated description for the flashcard group"
    )
    flashcards: List[FlashcardData] = Field(description="List of generated flashcards")


class FlashcardService:
    """Service for managing flashcards with AI generation capabilities."""

    def __init__(self, search_interface: SearchInterface):
        """Initialize the flashcard service."""
        self.credential = DefaultAzureCredential()
        self.search_interface = search_interface

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

        self.flashcard_parser = JsonOutputParser(
            pydantic_object=FlashcardGroupGenerationRequest
        )

    async def _get_project_documents_content(self, project_id: str) -> str:
        """Get all document content for a project."""
        try:
            # Search for all content in the project
            search_results = await self.search_interface.search_documents(
                query="",  # Empty query to get all content
                project_id=project_id,
                top_k=100,  # Get more content for better generation
            )

            if not search_results:
                return ""

            # Combine all content
            content_parts = []
            for result in search_results:
                content_parts.append(result.content)

            return "\n\n".join(content_parts)

        except Exception as e:
            logger.error("error getting project documents content: %s", e)
            return ""

    def _create_flashcard_group_prompt_template(self) -> PromptTemplate:
        """Create the prompt template for flashcard group generation."""
        template = """You are an expert educational content creator. Based on the following document content, generate a flashcard group with name, description, and {count} high-quality flashcards.

Document Content:
{document_content}

User Instructions: {user_prompt}

IMPORTANT: Generate all content in {language_code} language. All names, descriptions, questions, and answers must be in {language_code}.

Guidelines for flashcard group creation:
1. Generate a concise name (2-6 words) that captures the main topic or theme
2. Generate a description (1-2 sentences) explaining what the flashcards will cover
3. Create flashcards that test understanding, not just memorization
4. Include a mix of difficulty levels (easy, medium, hard)
5. Cover key concepts, definitions, important facts, and practical applications
6. Make questions clear and concise
7. Provide comprehensive but concise answers
8. Focus on the most important and educational content from the documents

{format_instructions}

Generate exactly {count} flashcards that are relevant to the document content and follow the user's instructions."""

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

    async def create_flashcard_group_with_flashcards(
        self,
        project_id: str,
        count: int = 30,
        user_prompt: Optional[str] = None,
    ) -> str:
        """Create a new flashcard group with auto-generated name, description, and flashcards."""
        with self._get_db_session() as db:
            try:
                logger.info(
                    "creating flashcard group with count=%d flashcards for project_id=%s",
                    count,
                    project_id,
                )

                # Generate all content using LangChain directly
                generated_content = await self._generate_flashcard_group_content(
                    db=db,
                    project_id=project_id,
                    count=count,
                    user_prompt=user_prompt,
                )

                name = generated_content["name"]
                description = generated_content["description"]
                flashcards_data = generated_content["flashcards"]

                logger.info(
                    "creating flashcard group name='%.100s...' for project_id=%s",
                    name,
                    project_id,
                )

                flashcard_group = FlashcardGroup(
                    id=str(uuid.uuid4()),
                    project_id=project_id,
                    name=name,
                    description=description,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )

                db.add(flashcard_group)

                logger.info("created flashcard_group_id=%s", flashcard_group.id)

                # Save flashcards to database
                for flashcard_item in flashcards_data:
                    flashcard = Flashcard(
                        id=str(uuid.uuid4()),
                        group_id=flashcard_group.id,
                        project_id=project_id,
                        question=flashcard_item.question,
                        answer=flashcard_item.answer,
                        difficulty_level=flashcard_item.difficulty_level,
                        created_at=datetime.now(),
                    )

                    db.add(flashcard)

                db.commit()

                logger.info("generated %d flashcards", len(flashcards_data))

                return str(flashcard_group.id)

            except Exception as e:
                logger.error("error creating flashcard group with flashcards: %s", e)
                raise

    async def _generate_flashcard_group_content(
        self,
        db: Session,
        project_id: str,
        count: int = 30,
        user_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate flashcard group name, description, and flashcards in one call."""
        try:
            logger.info(
                "generating flashcard group content for project_id=%s", project_id
            )

            project: Optional[Project] = (
                db.query(Project).filter(Project.id == project_id).first()
            )

            if not project:
                raise ValueError(f"Project {project_id} not found")

            language_code = project.language_code
            logger.info(
                "using language_code=%s for project_id=%s",
                language_code,
                project_id,
            )

            # Get project documents content
            document_content = await self._get_project_documents_content(project_id)
            if not document_content:
                raise ValueError(
                    "No documents found in project. Please upload documents first."
                )

            logger.info(
                "found %d chars of content in project_id=%s",
                len(document_content),
                project_id,
            )

            # Create prompt template
            prompt_template = self._create_flashcard_group_prompt_template()

            # Build the prompt
            prompt = prompt_template.format(
                document_content=document_content[
                    :8000
                ],  # Limit content to avoid token limits
                count=count,
                user_prompt=user_prompt
                or "Generate comprehensive flashcards covering key concepts, definitions, and important details.",
                language_code=language_code,
                format_instructions=self.flashcard_parser.get_format_instructions(),
            )

            # Generate content
            response = await self.llm.ainvoke(prompt)

            # Parse the response
            parsed_response = self.flashcard_parser.parse(response.content)

            # Handle both dict and object responses
            if isinstance(parsed_response, dict):
                return {
                    "name": parsed_response.get("name", "Flashcard Group"),
                    "description": parsed_response.get(
                        "description", "Auto-generated flashcard group"
                    ),
                    "flashcards": [
                        FlashcardData(**flashcard_dict)
                        for flashcard_dict in parsed_response.get("flashcards", [])
                    ],
                }
            else:
                return {
                    "name": parsed_response.name,
                    "description": parsed_response.description,
                    "flashcards": parsed_response.flashcards,
                }

        except Exception as e:
            logger.error("error generating flashcard group content: %s", e)
            raise

    def get_flashcard_groups(self, project_id: str) -> List[FlashcardGroup]:
        """Get all flashcard groups for a project."""
        with self._get_db_session() as db:
            try:
                logger.info("getting flashcard groups for project_id=%s", project_id)

                groups: list[FlashcardGroup] = (
                    db.query(FlashcardGroup)
                    .filter(FlashcardGroup.project_id == project_id)
                    .order_by(FlashcardGroup.created_at.desc())
                    .all()
                )

                logger.info("found %d flashcard groups", len(groups))
                return groups

            except Exception as e:
                logger.error("error getting flashcard groups: %s", e)
                raise

    def get_flashcard_group(self, group_id: str) -> Optional[FlashcardGroup]:
        """Get a specific flashcard group by ID."""
        with self._get_db_session() as db:
            try:
                logger.info("getting flashcard group_id=%s", group_id)

                group = (
                    db.query(FlashcardGroup)
                    .filter(FlashcardGroup.id == group_id)
                    .first()
                )

                if group:
                    logger.info("found flashcard group_id=%s", group_id)
                else:
                    logger.info("flashcard group_id=%s not found", group_id)

                return group

            except Exception as e:
                logger.error("error getting flashcard group: %s", e)
                raise

    def get_flashcards_by_group(self, group_id: str) -> List[Flashcard]:
        """Get all flashcards in a group."""
        with self._get_db_session() as db:
            try:
                logger.info("getting flashcards for group_id=%s", group_id)

                flashcards: list[Flashcard] = (
                    db.query(Flashcard)
                    .filter(Flashcard.group_id == group_id)
                    .order_by(Flashcard.created_at.asc())
                    .all()
                )

                logger.info("found %d flashcards", len(flashcards))
                return flashcards

            except Exception as e:
                logger.error("error getting flashcards: %s", e)
                raise

    def delete_flashcard_group(self, group_id: str) -> bool:
        """Delete a flashcard group and all its flashcards."""
        with self._get_db_session() as db:
            try:
                logger.info("deleting flashcard group_id=%s", group_id)

                group: Optional[FlashcardGroup] = (
                    db.query(FlashcardGroup)
                    .filter(FlashcardGroup.id == group_id)
                    .first()
                )

                if not group:
                    logger.warning("flashcard group_id=%s not found", group_id)
                    return False

                # Delete all flashcards in the group first (cascade should handle this)
                db.delete(group)
                db.commit()

                logger.info("deleted flashcard group_id=%s", group_id)
                return True

            except Exception as e:
                logger.error("error deleting flashcard group: %s", e)
                raise

    def update_flashcard_group(
        self,
        group_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[FlashcardGroup]:
        """Update a flashcard group."""
        with self._get_db_session() as db:
            try:
                logger.info("updating flashcard group_id=%s", group_id)

                group: Optional[FlashcardGroup] = (
                    db.query(FlashcardGroup)
                    .filter(FlashcardGroup.id == group_id)
                    .first()
                )
                if not group:
                    logger.warning("flashcard group_id=%s not found", group_id)
                    return None

                if name is not None:
                    group.name = name
                if description is not None:
                    group.description = description

                group.updated_at = datetime.now()

                db.commit()
                db.refresh(group)

                logger.info("updated flashcard group_id=%s", group_id)

                return group
            except Exception as e:
                logger.error("error updating flashcard group: %s", e)
                raise
