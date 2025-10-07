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
from db.model import FlashcardGroup, Flashcard, Project
from db.session import SessionLocal

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

    def __init__(self):
        """Initialize the flashcard service."""
        self._setup_langchain_components()
        self._setup_document_service()

    def _setup_langchain_components(self) -> None:
        """Initialize LangChain components for flashcard generation."""
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

        self.flashcard_parser = JsonOutputParser(
            pydantic_object=FlashcardGroupGenerationRequest
        )

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
    ) -> FlashcardGroup:
        """Create a new flashcard group with auto-generated name, description, and flashcards."""
        try:
            logger.info(
                f"Creating flashcard group with {count} flashcards for project {project_id}"
            )

            # Generate all content using LangChain directly
            generated_content = await self._generate_flashcard_group_content(
                project_id=project_id,
                count=count,
                user_prompt=user_prompt,
            )

            name = generated_content["name"]
            description = generated_content["description"]
            flashcards_data = generated_content["flashcards"]

            logger.info(f"Creating flashcard group '{name}' for project {project_id}")

            with self._get_db_session() as db:
                # Verify project exists
                project = db.query(Project).filter(Project.id == project_id).first()
                if not project:
                    raise ValueError(f"Project {project_id} not found")

                # Create flashcard group
                flashcard_group = FlashcardGroup(
                    id=str(uuid.uuid4()),
                    project_id=project_id,
                    name=name,
                    description=description,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )

                db.add(flashcard_group)
                db.commit()
                db.refresh(flashcard_group)

                logger.info(f"Created flashcard group: {flashcard_group.id}")

                # Save flashcards to database
                flashcard_ids = await self._save_flashcards_to_db(
                    flashcard_group.id, project_id, flashcards_data
                )

                logger.info(f"Generated and saved {len(flashcard_ids)} flashcards")
                return flashcard_group

        except Exception as e:
            logger.error(f"Error creating flashcard group with flashcards: {e}")
            raise

    async def _generate_flashcard_group_content(
        self,
        project_id: str,
        count: int = 30,
        user_prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate flashcard group name, description, and flashcards in one call."""
        try:
            logger.info(f"Generating flashcard group content for project {project_id}")

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
            logger.error(f"Error generating flashcard group content: {e}")
            raise

    async def _save_flashcards_to_db(
        self, group_id: str, project_id: str, flashcards_data: List[FlashcardData]
    ) -> List[str]:
        """Save generated flashcards to the database."""
        try:
            flashcard_ids = []

            with self._get_db_session() as db:
                for flashcard_data in flashcards_data:
                    flashcard = Flashcard(
                        id=str(uuid.uuid4()),
                        group_id=group_id,
                        project_id=project_id,
                        question=flashcard_data.question,
                        answer=flashcard_data.answer,
                        difficulty_level=flashcard_data.difficulty_level,
                        created_at=datetime.now(),
                    )

                    db.add(flashcard)
                    flashcard_ids.append(flashcard.id)

                db.commit()

            logger.info(f"Saved {len(flashcard_ids)} flashcards to database")
            return flashcard_ids

        except Exception as e:
            logger.error(f"Error saving flashcards to database: {e}")
            raise

    def get_flashcard_groups(self, project_id: str) -> List[FlashcardGroup]:
        """Get all flashcard groups for a project."""
        try:
            logger.info(f"Getting flashcard groups for project {project_id}")

            with self._get_db_session() as db:
                groups = (
                    db.query(FlashcardGroup)
                    .filter(FlashcardGroup.project_id == project_id)
                    .order_by(FlashcardGroup.created_at.desc())
                    .all()
                )

                logger.info(f"Found {len(groups)} flashcard groups")
                return groups

        except Exception as e:
            logger.error(f"Error getting flashcard groups: {e}")
            raise

    def get_flashcard_group(self, group_id: str) -> Optional[FlashcardGroup]:
        """Get a specific flashcard group by ID."""
        try:
            logger.info(f"Getting flashcard group {group_id}")

            with self._get_db_session() as db:
                group = (
                    db.query(FlashcardGroup)
                    .filter(FlashcardGroup.id == group_id)
                    .first()
                )

                if group:
                    logger.info(f"Found flashcard group: {group_id}")
                else:
                    logger.info(f"Flashcard group not found: {group_id}")

                return group

        except Exception as e:
            logger.error(f"Error getting flashcard group: {e}")
            raise

    def get_project_id_from_group(self, group_id: str) -> Optional[str]:
        """Get project_id from a flashcard group ID."""
        try:
            group = self.get_flashcard_group(group_id)
            return group.project_id if group else None
        except Exception as e:
            logger.error(f"Error getting project_id from group: {e}")
            return None

    def get_flashcards_by_group(self, group_id: str) -> List[Flashcard]:
        """Get all flashcards in a group."""
        try:
            logger.info(f"Getting flashcards for group {group_id}")

            with self._get_db_session() as db:
                flashcards = (
                    db.query(Flashcard)
                    .filter(Flashcard.group_id == group_id)
                    .order_by(Flashcard.created_at.asc())
                    .all()
                )

                logger.info(f"Found {len(flashcards)} flashcards")
                return flashcards

        except Exception as e:
            logger.error(f"Error getting flashcards: {e}")
            raise

    def get_flashcard(self, flashcard_id: str) -> Optional[Flashcard]:
        """Get a specific flashcard by ID."""
        try:
            logger.info(f"Getting flashcard {flashcard_id}")

            with self._get_db_session() as db:
                flashcard = (
                    db.query(Flashcard).filter(Flashcard.id == flashcard_id).first()
                )

                if flashcard:
                    logger.info(f"Found flashcard: {flashcard_id}")
                else:
                    logger.info(f"Flashcard not found: {flashcard_id}")

                return flashcard

        except Exception as e:
            logger.error(f"Error getting flashcard: {e}")
            raise

    def update_flashcard(
        self,
        flashcard_id: str,
        question: Optional[str] = None,
        answer: Optional[str] = None,
        difficulty_level: Optional[str] = None,
    ) -> Optional[Flashcard]:
        """Update a flashcard."""
        try:
            logger.info(f"Updating flashcard {flashcard_id}")

            with self._get_db_session() as db:
                flashcard = (
                    db.query(Flashcard).filter(Flashcard.id == flashcard_id).first()
                )

                if not flashcard:
                    logger.warning(f"Flashcard not found: {flashcard_id}")
                    return None

                if question is not None:
                    flashcard.question = question
                if answer is not None:
                    flashcard.answer = answer
                if difficulty_level is not None:
                    flashcard.difficulty_level = difficulty_level

                db.commit()
                db.refresh(flashcard)

                logger.info(f"Updated flashcard: {flashcard_id}")
                return flashcard

        except Exception as e:
            logger.error(f"Error updating flashcard: {e}")
            raise

    def delete_flashcard(self, flashcard_id: str) -> bool:
        """Delete a flashcard."""
        try:
            logger.info(f"Deleting flashcard {flashcard_id}")

            with self._get_db_session() as db:
                flashcard = (
                    db.query(Flashcard).filter(Flashcard.id == flashcard_id).first()
                )

                if not flashcard:
                    logger.warning(f"Flashcard not found: {flashcard_id}")
                    return False

                db.delete(flashcard)
                db.commit()

                logger.info(f"Deleted flashcard: {flashcard_id}")
                return True

        except Exception as e:
            logger.error(f"Error deleting flashcard: {e}")
            raise

    def delete_flashcard_group(self, group_id: str) -> bool:
        """Delete a flashcard group and all its flashcards."""
        try:
            logger.info(f"Deleting flashcard group {group_id}")

            with self._get_db_session() as db:
                group = (
                    db.query(FlashcardGroup)
                    .filter(FlashcardGroup.id == group_id)
                    .first()
                )

                if not group:
                    logger.warning(f"Flashcard group not found: {group_id}")
                    return False

                # Delete all flashcards in the group first (cascade should handle this)
                db.delete(group)
                db.commit()

                logger.info(f"Deleted flashcard group: {group_id}")
                return True

        except Exception as e:
            logger.error(f"Error deleting flashcard group: {e}")
            raise

    def update_flashcard_group(
        self,
        group_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[FlashcardGroup]:
        """Update a flashcard group."""
        try:
            logger.info(f"Updating flashcard group {group_id}")

            with self._get_db_session() as db:
                group = (
                    db.query(FlashcardGroup)
                    .filter(FlashcardGroup.id == group_id)
                    .first()
                )

                if not group:
                    logger.warning(f"Flashcard group not found: {group_id}")
                    return None

                if name is not None:
                    group.name = name
                if description is not None:
                    group.description = description

                group.updated_at = datetime.now()
                db.commit()
                db.refresh(group)

                logger.info(f"Updated flashcard group: {group_id}")
                return group

        except Exception as e:
            logger.error(f"Error updating flashcard group: {e}")
            raise
