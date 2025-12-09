"""Service for managing flashcards with AI generation capabilities."""

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
from core.logger import get_logger
from db.models import Flashcard, FlashcardGroup, Project
from db.session import SessionLocal
from schemas.flashcards import (
    FlashcardProgressUpdate,
    LENGTH_PREFERENCE_MAP,
    MAX_DOCUMENT_CONTENT_LENGTH,
    SEARCH_TOP_K_WITH_TOPIC,
    SEARCH_TOP_K_WITHOUT_TOPIC,
    FlashcardGroupGenerationRequest,
    FlashcardGroupGenerationResult,
)
from schemas.shared import (
    DifficultyLevel,
    GenerationProgressUpdate,
    GenerationStatus,
    LengthPreference,
)
from core.exceptions import NotFoundError, BadRequestError

logger = get_logger(__name__)


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

    def _resolve_count_from_length(
        self, length: Optional[LengthPreference]
    ) -> int:
        """Resolve length preference to flashcard count.
        
        Args:
            length: Length preference enum or None
            
        Returns:
            Resolved flashcard count
        """
        if length is None:
            length = LengthPreference.NORMAL
        return LENGTH_PREFERENCE_MAP[length]

    def _create_flashcard_group_and_flashcards(
        self,
        db: Session,
        project_id: str,
        content: FlashcardGroupGenerationResult,
    ) -> FlashcardGroup:
        """Create flashcard group and associated flashcards in database.
        
        Args:
            db: Database session
            project_id: The project ID
            content: Generated flashcard group content
            
        Returns:
            Created FlashcardGroup instance
        """
        group = FlashcardGroup(
            id=str(uuid.uuid4()),
            project_id=project_id,
            name=content.name,
            description=content.description,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.add(group)
        db.flush()

        for position, flashcard_item in enumerate(content.flashcards):
            flashcard = Flashcard(
                id=str(uuid.uuid4()),
                group_id=group.id,
                project_id=project_id,
                question=flashcard_item.question,
                answer=flashcard_item.answer,
                difficulty_level=flashcard_item.difficulty_level,
                position=position,
                created_at=datetime.now(),
            )
            db.add(flashcard)

        return group

    async def create_flashcard_group_with_flashcards(
        self,
        project_id: str,
        custom_instructions: Optional[str] = None,
        length: Optional[LengthPreference] = None,
        difficulty: Optional[DifficultyLevel] = None,
    ) -> str:
        """Create a new flashcard group with auto-generated name, description, and flashcards.

        Args:
            project_id: The project ID
            custom_instructions: Optional custom instructions including topic, format, length, and context
            length: Length preference enum
            difficulty: Difficulty level enum

        Returns:
            ID of the created flashcard group

        Raises:
            ValueError: If no documents found or generation fails
        """
        with self._get_db_session() as db:
            try:
                count = self._resolve_count_from_length(length)
                logger.info_structured(
                    "creating flashcard group",
                    project_id=project_id,
                    length=length.value if length else None,
                    count=count,
                )

                generated_content = await self._generate_flashcard_group_content(
                    db=db,
                    project_id=project_id,
                    count=count,
                    custom_instructions=custom_instructions,
                    difficulty=difficulty,
                )

                logger.info_structured(
                    "generated flashcard group content",
                    project_id=project_id,
                    group_name=generated_content.name[:100],
                    flashcard_count=len(generated_content.flashcards),
                )

                flashcard_group = self._create_flashcard_group_and_flashcards(
                    db=db,
                    project_id=project_id,
                    content=generated_content,
                )
                db.commit()

                logger.info_structured(
                    "created flashcard group",
                    flashcard_group_id=flashcard_group.id,
                    project_id=project_id,
                    flashcard_count=len(generated_content.flashcards),
                )

                return str(flashcard_group.id)
            except (NotFoundError, ValueError, BadRequestError):
                raise
            except Exception as e:
                logger.error_structured(
                    "error creating flashcard group",
                    project_id=project_id,
                    error=str(e),
                    exc_info=True,
                )
                raise

    async def create_flashcard_group_with_flashcards_stream(
        self,
        project_id: str,
        custom_instructions: Optional[str] = None,
        length: Optional[LengthPreference] = None,
        difficulty: Optional[DifficultyLevel] = None,
    ) -> AsyncGenerator[dict, None]:
        """Create a flashcard group with streaming progress updates.

        Args:
            project_id: The project ID
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

                count = self._resolve_count_from_length(length)
                yield GenerationProgressUpdate(
                    status=GenerationStatus.GENERATING
                ).model_dump(exclude_none=True)

                generated_content = await self._generate_flashcard_group_content(
                    db=db,
                    project_id=project_id,
                    count=count,
                    custom_instructions=custom_instructions,
                    difficulty=difficulty,
                )

                flashcard_group = self._create_flashcard_group_and_flashcards(
                    db=db,
                    project_id=project_id,
                    content=generated_content,
                )
                db.commit()

                logger.info_structured(
                    "generated flashcards",
                    flashcard_group_id=flashcard_group.id,
                    flashcard_count=len(generated_content.flashcards),
                    project_id=project_id,
                )

                yield FlashcardProgressUpdate(
                    status=GenerationStatus.DONE,
                    group_id=str(flashcard_group.id),
                ).model_dump(exclude_none=True)

        except (NotFoundError, ValueError, BadRequestError) as e:
            logger.error_structured(
                "error creating flashcard group",
                project_id=project_id,
                error=str(e),
            )
            yield GenerationProgressUpdate(
                status=GenerationStatus.DONE,
                error=str(e),
            ).model_dump(exclude_none=True)
        except Exception as e:
            logger.error_structured(
                "error creating flashcard group",
                project_id=project_id,
                error=str(e),
                exc_info=True,
            )
            yield GenerationProgressUpdate(
                status=GenerationStatus.DONE,
                error="Failed to create flashcards. Please try again.",
            ).model_dump(exclude_none=True)

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

                logger.info_structured(
                    "found flashcard groups",
                    count=len(groups),
                    project_id=project_id,
                )
                return groups
            except Exception as e:
                logger.error_structured(
                    "error getting flashcard groups",
                    project_id=project_id,
                    error=str(e),
                    exc_info=True,
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

                if not group:
                    logger.warning_structured(
                        "flashcard group not found",
                        group_id=group_id,
                    )
                else:
                    logger.info_structured(
                        "found flashcard group",
                        group_id=group_id,
                    )

                return group
            except Exception as e:
                logger.error_structured(
                    "error getting flashcard group",
                    group_id=group_id,
                    error=str(e),
                    exc_info=True,
                )
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

                logger.info_structured(
                    "found flashcards",
                    count=len(flashcards),
                    group_id=group_id,
                )
                return flashcards
            except Exception as e:
                logger.error_structured(
                    "error getting flashcards",
                    group_id=group_id,
                    error=str(e),
                    exc_info=True,
                )
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

                logger.info_structured(
                    "deleted flashcard group",
                    group_id=group_id,
                )
                return True
            except Exception as e:
                logger.error_structured(
                    "error deleting flashcard group",
                    group_id=group_id,
                    error=str(e),
                    exc_info=True,
                )
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

                logger.info_structured(
                    "updated flashcard group",
                    group_id=group_id,
                )

                return group
            except Exception as e:
                logger.error_structured(
                    "error updating flashcard group",
                    group_id=group_id,
                    error=str(e),
                    exc_info=True,
                )
                raise

    def create_flashcard(
        self,
        group_id: str,
        project_id: str,
        question: str,
        answer: str,
        difficulty_level: DifficultyLevel = DifficultyLevel.MEDIUM,
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
                    difficulty_level=difficulty_level.value,
                    position=position,
                )

                db.add(flashcard)
                db.commit()
                db.refresh(flashcard)

                logger.info_structured(
                    "created flashcard",
                    flashcard_id=flashcard.id,
                    group_id=group_id,
                    project_id=project_id,
                )
                return flashcard
            except (NotFoundError, ValueError):
                raise
            except Exception as e:
                logger.error_structured(
                    "error creating flashcard",
                    group_id=group_id,
                    project_id=project_id,
                    error=str(e),
                    exc_info=True,
                )
                raise

    def update_flashcard(
        self,
        flashcard_id: str,
        question: Optional[str] = None,
        answer: Optional[str] = None,
        difficulty_level: Optional[DifficultyLevel] = None,
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
                    flashcard.difficulty_level = difficulty_level.value

                db.commit()
                db.refresh(flashcard)

                logger.info_structured(
                    "updated flashcard",
                    flashcard_id=flashcard_id,
                )
                return flashcard
            except Exception as e:
                logger.error_structured(
                    "error updating flashcard",
                    flashcard_id=flashcard_id,
                    error=str(e),
                    exc_info=True,
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
                logger.info_structured(
                    "reordering flashcards",
                    group_id=group_id,
                    flashcard_count=len(flashcard_ids),
                )

                group = (
                    db.query(FlashcardGroup)
                    .filter(FlashcardGroup.id == group_id)
                    .first()
                )
                if not group:
                    raise NotFoundError(f"Flashcard group {group_id} not found")

                flashcards = (
                    db.query(Flashcard).filter(Flashcard.group_id == group_id).all()
                )
                flashcard_dict = {f.id: f for f in flashcards}

                for flashcard_id in flashcard_ids:
                    if flashcard_id not in flashcard_dict:
                        raise NotFoundError(
                            f"Flashcard {flashcard_id} not found in group {group_id}"
                        )

                updated_flashcards = []
                for position, flashcard_id in enumerate(flashcard_ids):
                    flashcard = flashcard_dict[flashcard_id]
                    flashcard.position = position
                    updated_flashcards.append(flashcard)

                db.commit()
                for flashcard in updated_flashcards:
                    db.refresh(flashcard)

                logger.info_structured(
                    "reordered flashcards",
                    count=len(updated_flashcards),
                    group_id=group_id,
                )
                return updated_flashcards
            except (NotFoundError, ValueError):
                raise
            except Exception as e:
                logger.error_structured(
                    "error reordering flashcards",
                    group_id=group_id,
                    error=str(e),
                    exc_info=True,
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

                logger.info_structured(
                    "deleted flashcard",
                    flashcard_id=flashcard_id,
                )
                return True
            except Exception as e:
                logger.error_structured(
                    "error deleting flashcard",
                    flashcard_id=flashcard_id,
                    error=str(e),
                    exc_info=True,
                )
                raise

    async def _generate_flashcard_group_content(
        self,
        db: Session,
        project_id: str,
        count: int,
        custom_instructions: Optional[str] = None,
        difficulty: Optional[DifficultyLevel] = None,
    ) -> FlashcardGroupGenerationResult:
        """Generate flashcard group name, description, and flashcards in one call.

        Args:
            db: Database session
            project_id: The project ID
            count: Number of flashcards to generate
            custom_instructions: Optional custom instructions including topic, format, length, and context
            difficulty: Difficulty level enum

        Returns:
            FlashcardGroupGenerationResult containing name, description, and flashcards

        Raises:
            NotFoundError: If project not found
            ValueError: If no documents available
        """
        try:
            logger.info_structured(
                "generating flashcard group content",
                project_id=project_id,
                count=count,
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

            prompt = render_prompt(
                "flashcard_group_prompt",
                document_content=document_content[:MAX_DOCUMENT_CONTENT_LENGTH],
                count=count,
                custom_instructions=custom_instructions or "",
                language_code=language_code,
                difficulty=difficulty.value if difficulty else None,
                format_instructions=self.flashcard_parser.get_format_instructions(),
            )

            response = await self.llm.ainvoke(prompt)
            parsed_dict = self.flashcard_parser.parse(response.content)
            generation_request = FlashcardGroupGenerationRequest(**parsed_dict)

            return FlashcardGroupGenerationResult(
                name=generation_request.name,
                description=generation_request.description,
                flashcards=generation_request.flashcards,
            )
        except (NotFoundError, ValueError):
            raise
        except Exception as e:
            logger.error_structured(
                "error generating flashcard group content",
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
