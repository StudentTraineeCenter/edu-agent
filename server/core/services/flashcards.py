"""Service for managing flashcards with AI generation capabilities."""

import uuid
from contextlib import contextmanager
from datetime import datetime
from typing import AsyncGenerator, List, Optional

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import AzureChatOpenAI
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from core.agents.search import SearchInterface
from core.config import app_config
from core.logger import get_logger
from db.models import Flashcard, FlashcardGroup, Project
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


class FlashcardGroupGenerationResult(BaseModel):
    """Model for flashcard group generation result."""

    name: str
    description: str
    flashcards: List[FlashcardData]


class FlashcardService:
    """Service for managing flashcards with AI generation capabilities."""

    def __init__(self, search_interface: SearchInterface) -> None:
        """Initialize the flashcard service.

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

        self.flashcard_parser = JsonOutputParser(
            pydantic_object=FlashcardGroupGenerationRequest
        )

    async def create_flashcard_group_with_flashcards(
        self,
        project_id: str,
        count: int = 30,
        user_prompt: Optional[str] = None,
    ) -> str:
        """Create a new flashcard group with auto-generated name, description, and flashcards.

        Args:
            project_id: The project ID
            count: Number of flashcards to generate
            user_prompt: Optional user instructions for generation

        Returns:
            ID of the created flashcard group

        Raises:
            ValueError: If no documents found or generation fails
        """
        with self._get_db_session() as db:
            try:
                logger.info(
                    f"creating flashcard group with count={count} flashcards for project_id={project_id}"
                )

                # Generate all content using LangChain directly
                generated_content = await self._generate_flashcard_group_content(
                    db=db,
                    project_id=project_id,
                    count=count,
                    user_prompt=user_prompt,
                )

                name = generated_content.name
                description = generated_content.description
                flashcards_data = generated_content.flashcards

                logger.info(
                    f"creating flashcard group name='{name[:100]}...' for project_id={project_id}"
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

                logger.info(f"created flashcard_group_id={flashcard_group.id}")

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

                logger.info(f"generated {len(flashcards_data)} flashcards")

                return str(flashcard_group.id)
            except ValueError:
                raise
            except Exception as e:
                logger.error(
                    f"error creating flashcard group for project_id={project_id}: {e}"
                )
                raise

    async def create_flashcard_group_with_flashcards_stream(
        self,
        project_id: str,
        count: int = 30,
        user_prompt: Optional[str] = None,
    ) -> AsyncGenerator[dict, None]:
        """Create a flashcard group with streaming progress updates.

        Args:
            project_id: The project ID
            count: Number of flashcards to generate
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

                yield {"status": "analyzing", "message": "Identifying key concepts..."}

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
                    "message": f"Generating {count} flashcards...",
                }

                # Generate content
                generated_content = await self._generate_flashcard_group_content(
                    db=db,
                    project_id=project_id,
                    count=count,
                    user_prompt=user_prompt,
                )

                name = generated_content.name
                description = generated_content.description
                flashcards_data = generated_content.flashcards

                # Create flashcard group in database
                flashcard_group = FlashcardGroup(
                    id=str(uuid.uuid4()),
                    project_id=project_id,
                    name=name,
                    description=description,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
                db.add(flashcard_group)
                db.flush()  # Flush to get group.id

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

                logger.info(f"generated {len(flashcards_data)} flashcards")

                yield {
                    "status": "done",
                    "message": "Flashcards created successfully",
                    "group_id": str(flashcard_group.id),
                }

        except ValueError as e:
            logger.error(f"error creating flashcard group: {e}")
            yield {
                "status": "done",
                "message": "Error creating flashcards",
                "error": str(e),
            }
        except Exception as e:
            logger.error(f"error creating flashcard group: {e}", exc_info=True)
            yield {
                "status": "done",
                "message": "Error creating flashcards",
                "error": "Failed to create flashcards. Please try again.",
            }

    def get_flashcard_groups(self, project_id: str) -> List[FlashcardGroup]:
        """Get all flashcard groups for a project.

        Args:
            project_id: The project ID

        Returns:
            List of FlashcardGroup model instances
        """
        with self._get_db_session() as db:
            try:
                logger.info(f"getting flashcard groups for project_id={project_id}")

                groups = (
                    db.query(FlashcardGroup)
                    .filter(
                        FlashcardGroup.project_id == project_id,
                        FlashcardGroup.study_session_id.is_(
                            None
                        ),  # Exclude study session groups
                    )
                    .order_by(FlashcardGroup.created_at.desc())
                    .all()
                )

                logger.info(f"found {len(groups)} flashcard groups")
                return groups
            except Exception as e:
                logger.error(
                    f"error getting flashcard groups for project_id={project_id}: {e}"
                )
                raise

    def get_flashcard_group(self, group_id: str) -> Optional[FlashcardGroup]:
        """Get a specific flashcard group by ID.

        Args:
            group_id: The flashcard group ID

        Returns:
            FlashcardGroup model instance or None if not found
        """
        with self._get_db_session() as db:
            try:
                logger.info(f"getting flashcard group_id={group_id}")

                group = (
                    db.query(FlashcardGroup)
                    .filter(FlashcardGroup.id == group_id)
                    .first()
                )

                if group:
                    logger.info(f"found flashcard group_id={group_id}")
                else:
                    logger.info(f"flashcard group_id={group_id} not found")

                return group
            except Exception as e:
                logger.error(f"error getting flashcard group group_id={group_id}: {e}")
                raise

    def get_flashcards_by_group(self, group_id: str) -> List[Flashcard]:
        """Get all flashcards in a group.

        Args:
            group_id: The flashcard group ID

        Returns:
            List of Flashcard model instances
        """
        with self._get_db_session() as db:
            try:
                logger.info(f"getting flashcards for group_id={group_id}")

                flashcards = (
                    db.query(Flashcard)
                    .filter(Flashcard.group_id == group_id)
                    .order_by(Flashcard.created_at.asc())
                    .all()
                )

                logger.info(f"found {len(flashcards)} flashcards")
                return flashcards
            except Exception as e:
                logger.error(f"error getting flashcards for group_id={group_id}: {e}")
                raise

    def delete_flashcard_group(self, group_id: str) -> bool:
        """Delete a flashcard group and all its flashcards.

        Args:
            group_id: The flashcard group ID

        Returns:
            True if deleted successfully, False if not found
        """
        with self._get_db_session() as db:
            try:
                logger.info(f"deleting flashcard group_id={group_id}")

                group = (
                    db.query(FlashcardGroup)
                    .filter(FlashcardGroup.id == group_id)
                    .first()
                )

                if not group:
                    logger.warning(f"flashcard group_id={group_id} not found")
                    return False

                # Delete all flashcards in the group first (cascade should handle this)
                db.delete(group)
                db.commit()

                logger.info(f"deleted flashcard group_id={group_id}")
                return True
            except Exception as e:
                logger.error(f"error deleting flashcard group group_id={group_id}: {e}")
                raise

    def update_flashcard_group(
        self,
        group_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[FlashcardGroup]:
        """Update a flashcard group.

        Args:
            group_id: The flashcard group ID
            name: Optional new name
            description: Optional new description

        Returns:
            Updated FlashcardGroup model instance or None if not found
        """
        with self._get_db_session() as db:
            try:
                logger.info(f"updating flashcard group_id={group_id}")

                group = (
                    db.query(FlashcardGroup)
                    .filter(FlashcardGroup.id == group_id)
                    .first()
                )
                if not group:
                    logger.warning(f"flashcard group_id={group_id} not found")
                    return None

                if name is not None:
                    group.name = name
                if description is not None:
                    group.description = description

                group.updated_at = datetime.now()

                db.commit()
                db.refresh(group)

                logger.info(f"updated flashcard group_id={group_id}")

                return group
            except Exception as e:
                logger.error(f"error updating flashcard group group_id={group_id}: {e}")
                raise

    async def _generate_flashcard_group_content(
        self,
        db: Session,
        project_id: str,
        count: int = 30,
        user_prompt: Optional[str] = None,
    ) -> FlashcardGroupGenerationResult:
        """Generate flashcard group name, description, and flashcards in one call.

        Args:
            db: Database session
            project_id: The project ID
            count: Number of flashcards to generate
            user_prompt: Optional user instructions

        Returns:
            FlashcardGroupGenerationResult containing name, description, and flashcards

        Raises:
            ValueError: If project not found or no documents available
        """
        try:
            logger.info(
                f"generating flashcard group content for project_id={project_id}"
            )

            project = db.query(Project).filter(Project.id == project_id).first()

            if not project:
                raise ValueError(f"Project {project_id} not found")

            language_code = project.language_code
            logger.info(
                f"using language_code={language_code} for project_id={project_id}"
            )

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

            # Parse the response - JsonOutputParser returns dict, convert to FlashcardGroupGenerationRequest
            parsed_dict = self.flashcard_parser.parse(response.content)
            generation_request = FlashcardGroupGenerationRequest(**parsed_dict)

            return FlashcardGroupGenerationResult(
                name=generation_request.name,
                description=generation_request.description,
                flashcards=generation_request.flashcards,
            )
        except ValueError:
            raise
        except Exception as e:
            logger.error(
                f"error generating flashcard group content for project_id={project_id}: {e}"
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

    def _create_flashcard_group_prompt_template(self) -> PromptTemplate:
        """Create the prompt template for flashcard group generation.

        Returns:
            PromptTemplate instance
        """
        template = """You are an expert educational content creator specializing in creating effective learning materials. Your goal is to help students master the course material through well-designed flashcards that promote deep understanding.

Document Content:
{document_content}

User Instructions: {user_prompt}

CRITICAL LANGUAGE REQUIREMENT: You MUST generate ALL content in {language_code} language. This includes:
- Group name and description
- All flashcard questions
- All flashcard answers
- Any explanations or additional context
Never use any language other than {language_code}. If the document content is in a different language, translate all relevant information to {language_code}.

Educational Guidelines for flashcard creation:
1. Name: Generate a concise, descriptive name (2-6 words) that captures the main topic or theme in {language_code}
2. Description: Generate a clear description (1-2 sentences) in {language_code} explaining what knowledge the flashcards will help students master
3. Learning-focused questions: Create flashcards that test understanding, application, and critical thinking - not just rote memorization
4. Difficulty distribution: Include a balanced mix of difficulty levels (easy: foundational concepts, medium: application, hard: analysis/synthesis)
5. Comprehensive coverage: Cover key concepts, definitions, important facts, relationships between ideas, and practical applications
6. Question quality: Make questions clear, specific, and thought-provoking - they should require understanding, not just recall
7. Answer quality: Provide comprehensive but concise answers that explain the "why" behind the concept, not just the "what"
8. Educational value: Focus on the most pedagogically important content that will help students truly understand the material
9. Progressive learning: Structure flashcards to build from basic concepts to more complex applications
10. Active recall: Design questions that require active retrieval and application of knowledge

{format_instructions}

Generate exactly {count} high-quality flashcards in {language_code} that are relevant to the document content, follow the user's instructions, and promote deep learning."""

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
