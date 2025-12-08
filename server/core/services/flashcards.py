"""Service for managing flashcards with AI generation capabilities."""

import uuid
from contextlib import contextmanager
from datetime import datetime
from typing import AsyncGenerator, List, Optional

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import AzureChatOpenAI
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from core.agents.prompts_utils import render_prompt
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

    def _resolve_flashcard_count(
        self, count: int, length: Optional[str] = None
    ) -> int:
        """Resolve length preference to actual flashcard count.
        
        Args:
            count: Base count (used if length is None or 'normal')
            length: Length preference: 'less', 'normal', or 'more'
            
        Returns:
            Resolved flashcard count
        """
        if length == "less":
            return 15
        elif length == "more":
            return 50
        else:  # normal or None
            return count

    async def create_flashcard_group_with_flashcards(
        self,
        project_id: str,
        count: int = 30,
        user_prompt: Optional[str] = None,
        length: Optional[str] = None,
        difficulty: Optional[str] = None,
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
                # Resolve length to actual count
                resolved_count = self._resolve_flashcard_count(count, length)
                logger.info(
                    f"creating flashcard group with count={resolved_count} flashcards for project_id={project_id} (length={length})"
                )

                # Generate all content using LangChain directly
                generated_content = await self._generate_flashcard_group_content(
                    db=db,
                    project_id=project_id,
                    count=resolved_count,
                    user_prompt=user_prompt,
                    length=None,  # Don't pass length to prompt, already resolved to count
                    difficulty=difficulty,
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

                logger.info_structured("created flashcard group", flashcard_group_id=flashcard_group.id, project_id=project_id)

                # Save flashcards to database
                for position, flashcard_item in enumerate(flashcards_data):
                    flashcard = Flashcard(
                        id=str(uuid.uuid4()),
                        group_id=flashcard_group.id,
                        project_id=project_id,
                        question=flashcard_item.question,
                        answer=flashcard_item.answer,
                        difficulty_level=flashcard_item.difficulty_level,
                        position=position,
                        created_at=datetime.now(),
                    )
                    db.add(flashcard)

                db.commit()

                logger.info_structured("generated flashcards", count=len(flashcards_data), project_id=project_id)

                return str(flashcard_group.id)
            except ValueError:
                raise
            except Exception as e:
                logger.error_structured("error creating flashcard group", project_id=project_id, error=str(e), exc_info=True)
                raise

    async def create_flashcard_group_with_flashcards_stream(
        self,
        project_id: str,
        count: int = 30,
        user_prompt: Optional[str] = None,
        length: Optional[str] = None,
        difficulty: Optional[str] = None,
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

                # Resolve length to actual count
                resolved_count = self._resolve_flashcard_count(count, length)
                yield {
                    "status": "generating",
                    "message": f"Generating {resolved_count} flashcards...",
                }

                # Generate content
                generated_content = await self._generate_flashcard_group_content(
                    db=db,
                    project_id=project_id,
                    count=resolved_count,
                    user_prompt=user_prompt,
                    length=None,  # Don't pass length to prompt, already resolved to count
                    difficulty=difficulty,
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
                for position, flashcard_item in enumerate(flashcards_data):
                    flashcard = Flashcard(
                        id=str(uuid.uuid4()),
                        group_id=flashcard_group.id,
                        project_id=project_id,
                        question=flashcard_item.question,
                        answer=flashcard_item.answer,
                        difficulty_level=flashcard_item.difficulty_level,
                        position=position,
                        created_at=datetime.now(),
                    )
                    db.add(flashcard)

                db.commit()

                logger.info_structured("generated flashcards", count=len(flashcards_data), project_id=project_id)

                yield {
                    "status": "done",
                    "message": "Flashcards created successfully",
                    "group_id": str(flashcard_group.id),
                }

        except ValueError as e:
            logger.error_structured("error creating flashcard group", project_id=project_id, error=str(e))
            yield {
                "status": "done",
                "message": "Error creating flashcards",
                "error": str(e),
            }
        except Exception as e:
            logger.error_structured("error creating flashcard group", project_id=project_id, error=str(e), exc_info=True)
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
                logger.info_structured("getting flashcard groups", project_id=project_id)

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

                logger.info_structured("found flashcard groups", count=len(groups), project_id=project_id)
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
                logger.info_structured("getting flashcard group", group_id=group_id)

                group = (
                    db.query(FlashcardGroup)
                    .filter(FlashcardGroup.id == group_id)
                    .first()
                )

                if group:
                    logger.info_structured("found flashcard group", group_id=group_id)
                else:
                    logger.info_structured("flashcard group not found", group_id=group_id)

                return group
            except Exception as e:
                logger.error_structured("error getting flashcard group", group_id=group_id, error=str(e), exc_info=True)
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
                logger.info_structured("getting flashcards", group_id=group_id)

                flashcards = (
                    db.query(Flashcard)
                    .filter(Flashcard.group_id == group_id)
                    .order_by(Flashcard.position.asc(), Flashcard.created_at.asc())
                    .all()
                )

                logger.info_structured("found flashcards", count=len(flashcards), group_id=group_id)
                return flashcards
            except Exception as e:
                logger.error_structured("error getting flashcards", group_id=group_id, error=str(e), exc_info=True)
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
                logger.info_structured("deleting flashcard group", group_id=group_id)

                group = (
                    db.query(FlashcardGroup)
                    .filter(FlashcardGroup.id == group_id)
                    .first()
                )

                if not group:
                    logger.warning_structured("flashcard group not found", group_id=group_id)
                    return False

                # Delete all flashcards in the group first (cascade should handle this)
                db.delete(group)
                db.commit()

                logger.info_structured("deleted flashcard group", group_id=group_id)
                return True
            except Exception as e:
                logger.error_structured("error deleting flashcard group", group_id=group_id, error=str(e), exc_info=True)
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
                logger.info_structured("updating flashcard group", group_id=group_id)

                group = (
                    db.query(FlashcardGroup)
                    .filter(FlashcardGroup.id == group_id)
                    .first()
                )
                if not group:
                    logger.warning_structured("flashcard group not found", group_id=group_id)
                    return None

                if name is not None:
                    group.name = name
                if description is not None:
                    group.description = description

                group.updated_at = datetime.now()

                db.commit()
                db.refresh(group)

                logger.info_structured("updated flashcard group", group_id=group_id)

                return group
            except Exception as e:
                logger.error_structured("error updating flashcard group", group_id=group_id, error=str(e), exc_info=True)
                raise

    def create_flashcard(
        self,
        group_id: str,
        project_id: str,
        question: str,
        answer: str,
        difficulty_level: str = "medium",
        position: Optional[int] = None,
    ) -> Flashcard:
        """Create a new flashcard.

        Args:
            group_id: The flashcard group ID
            project_id: The project ID
            question: The flashcard question
            answer: The flashcard answer
            difficulty_level: Difficulty level (easy, medium, hard)
            position: Optional position for ordering. If None, appends to end.

        Returns:
            Created Flashcard model instance

        Raises:
            ValueError: If group not found
        """
        with self._get_db_session() as db:
            try:
                logger.info_structured("creating flashcard", group_id=group_id, project_id=project_id)

                # Verify group exists
                group = (
                    db.query(FlashcardGroup)
                    .filter(FlashcardGroup.id == group_id)
                    .first()
                )
                if not group:
                    raise ValueError(f"Flashcard group {group_id} not found")

                # If position not provided, get the max position and add 1
                if position is None:
                    max_position = (
                        db.query(func.max(Flashcard.position))
                        .filter(Flashcard.group_id == group_id)
                        .scalar()
                    )
                    position = (max_position or -1) + 1

                flashcard = Flashcard(
                    group_id=group_id,
                    project_id=project_id,
                    question=question,
                    answer=answer,
                    difficulty_level=difficulty_level,
                    position=position,
                )

                db.add(flashcard)
                db.commit()
                db.refresh(flashcard)

                logger.info_structured("created flashcard", flashcard_id=flashcard.id, group_id=group_id, project_id=project_id)
                return flashcard
            except ValueError:
                raise
            except Exception as e:
                logger.error_structured("error creating flashcard", group_id=group_id, project_id=project_id, error=str(e), exc_info=True)
                raise

    def update_flashcard(
        self,
        flashcard_id: str,
        question: Optional[str] = None,
        answer: Optional[str] = None,
        difficulty_level: Optional[str] = None,
    ) -> Optional[Flashcard]:
        """Update an existing flashcard.

        Args:
            flashcard_id: The flashcard ID
            question: Optional new question
            answer: Optional new answer
            difficulty_level: Optional new difficulty level

        Returns:
            Updated Flashcard model instance or None if not found
        """
        with self._get_db_session() as db:
            try:
                logger.info_structured("updating flashcard", flashcard_id=flashcard_id)

                flashcard = (
                    db.query(Flashcard).filter(Flashcard.id == flashcard_id).first()
                )
                if not flashcard:
                    logger.warning_structured("flashcard not found", flashcard_id=flashcard_id)
                    return None

                if question is not None:
                    flashcard.question = question
                if answer is not None:
                    flashcard.answer = answer
                if difficulty_level is not None:
                    flashcard.difficulty_level = difficulty_level

                db.commit()
                db.refresh(flashcard)

                logger.info_structured("updated flashcard", flashcard_id=flashcard_id)
                return flashcard
            except Exception as e:
                logger.error(
                    f"error updating flashcard flashcard_id={flashcard_id}: {e}"
                )
                raise

    def reorder_flashcards(
        self, group_id: str, flashcard_ids: List[str]
    ) -> List[Flashcard]:
        """Reorder flashcards in a group.

        Args:
            group_id: The flashcard group ID
            flashcard_ids: List of flashcard IDs in the desired order

        Returns:
            List of updated Flashcard model instances

        Raises:
            ValueError: If group not found or flashcard IDs don't match group
        """
        with self._get_db_session() as db:
            try:
                logger.info(
                    f"reordering flashcards for group_id={group_id}, count={len(flashcard_ids)}"
                )

                # Verify group exists
                group = (
                    db.query(FlashcardGroup)
                    .filter(FlashcardGroup.id == group_id)
                    .first()
                )
                if not group:
                    raise ValueError(f"Flashcard group {group_id} not found")

                # Get all flashcards in the group
                flashcards = (
                    db.query(Flashcard).filter(Flashcard.group_id == group_id).all()
                )
                flashcard_dict = {f.id: f for f in flashcards}

                # Verify all provided IDs exist and belong to the group
                for flashcard_id in flashcard_ids:
                    if flashcard_id not in flashcard_dict:
                        raise ValueError(
                            f"Flashcard {flashcard_id} not found in group {group_id}"
                        )

                # Update positions based on the order in flashcard_ids
                updated_flashcards = []
                for position, flashcard_id in enumerate(flashcard_ids):
                    flashcard = flashcard_dict[flashcard_id]
                    flashcard.position = position
                    updated_flashcards.append(flashcard)

                db.commit()
                for flashcard in updated_flashcards:
                    db.refresh(flashcard)

                logger.info_structured("reordered flashcards", count=len(updated_flashcards), group_id=group_id)
                return updated_flashcards
            except ValueError:
                raise
            except Exception as e:
                logger.error(
                    f"error reordering flashcards for group_id={group_id}: {e}"
                )
                raise

    def delete_flashcard(self, flashcard_id: str) -> bool:
        """Delete a flashcard.

        Args:
            flashcard_id: The flashcard ID

        Returns:
            True if deleted successfully, False if not found
        """
        with self._get_db_session() as db:
            try:
                logger.info_structured("deleting flashcard", flashcard_id=flashcard_id)

                flashcard = (
                    db.query(Flashcard).filter(Flashcard.id == flashcard_id).first()
                )

                if not flashcard:
                    logger.warning_structured("flashcard not found", flashcard_id=flashcard_id)
                    return False

                db.delete(flashcard)
                db.commit()

                logger.info_structured("deleted flashcard", flashcard_id=flashcard_id)
                return True
            except Exception as e:
                logger.error(
                    f"error deleting flashcard flashcard_id={flashcard_id}: {e}"
                )
                raise

    async def _generate_flashcard_group_content(
        self,
        db: Session,
        project_id: str,
        count: int = 30,
        user_prompt: Optional[str] = None,
        length: Optional[str] = None,
        difficulty: Optional[str] = None,
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

            # Build difficulty instructions (length is already resolved to count)
            difficulty_instruction = ""
            if difficulty == "easy":
                difficulty_instruction = " Focus on basic concepts and straightforward flashcards suitable for beginners."
            elif difficulty == "hard":
                difficulty_instruction = " Create challenging flashcards that test deep understanding, analysis, and application of concepts."
            # "medium" or None uses default behavior

            # Build the prompt using Jinja2 template
            prompt = render_prompt(
                "flashcard_group_prompt",
                document_content=document_content[
                    :8000
                ],  # Limit content to avoid token limits
                count=count,
                user_prompt=(user_prompt
                or "Generate comprehensive flashcards covering key concepts, definitions, and important details.")
                + difficulty_instruction,
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
