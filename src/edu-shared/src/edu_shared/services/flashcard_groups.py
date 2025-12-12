"""CRUD service for managing flashcard groups."""

from contextlib import contextmanager
from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from edu_shared.db.models import FlashcardGroup, Flashcard
from edu_shared.db.session import get_session_factory
from edu_shared.schemas.flashcards import FlashcardGroupDto, FlashcardDto
from edu_shared.exceptions import NotFoundError
from edu_shared.agents.flashcard_agent import FlashcardAgent
from edu_shared.agents.base import ContentAgentConfig
from edu_shared.services.search import SearchService


class FlashcardGroupService:
    """Service for managing flashcard groups."""

    def __init__(self) -> None:
        """Initialize the flashcard group service."""
        pass

    def create_flashcard_group(
        self,
        project_id: str,
        name: str,
        description: Optional[str] = None,
        study_session_id: Optional[str] = None,
    ) -> FlashcardGroupDto:
        """Create a new flashcard group.

        Args:
            project_id: The project ID
            name: The flashcard group name
            description: Optional group description
            study_session_id: Optional study session ID

        Returns:
            Created FlashcardGroupDto
        """
        with self._get_db_session() as db:
            try:
                flashcard_group = FlashcardGroup(
                    id=str(uuid4()),
                    project_id=project_id,
                    name=name,
                    description=description,
                    study_session_id=study_session_id,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
                db.add(flashcard_group)
                db.commit()
                db.refresh(flashcard_group)

                return self._model_to_dto(flashcard_group)
            except Exception as e:
                db.rollback()
                raise

    def get_flashcard_group(self, group_id: str, project_id: str) -> FlashcardGroupDto:
        """Get a flashcard group by ID.

        Args:
            group_id: The flashcard group ID
            project_id: The project ID

        Returns:
            FlashcardGroupDto

        Raises:
            NotFoundError: If flashcard group not found
        """
        with self._get_db_session() as db:
            try:
                flashcard_group = (
                    db.query(FlashcardGroup)
                    .filter(
                        FlashcardGroup.id == group_id,
                        FlashcardGroup.project_id == project_id,
                    )
                    .first()
                )
                if not flashcard_group:
                    raise NotFoundError(f"Flashcard group {group_id} not found")

                return self._model_to_dto(flashcard_group)
            except NotFoundError:
                raise
            except Exception as e:
                raise

    def list_flashcard_groups(
        self, project_id: str, study_session_id: Optional[str] = None
    ) -> List[FlashcardGroupDto]:
        """List all flashcard groups for a project.

        Args:
            project_id: The project ID
            study_session_id: Optional study session ID to filter by (None to exclude study session groups)

        Returns:
            List of FlashcardGroupDto instances
        """
        with self._get_db_session() as db:
            try:
                query = db.query(FlashcardGroup).filter(FlashcardGroup.project_id == project_id)
                if study_session_id is not None:
                    query = query.filter(FlashcardGroup.study_session_id == study_session_id)
                else:
                    # Exclude groups that belong to study sessions by default
                    query = query.filter(FlashcardGroup.study_session_id.is_(None))
                flashcard_groups = query.order_by(FlashcardGroup.created_at.desc()).all()
                return [self._model_to_dto(group) for group in flashcard_groups]
            except Exception as e:
                raise

    def update_flashcard_group(
        self,
        group_id: str,
        project_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> FlashcardGroupDto:
        """Update a flashcard group.

        Args:
            group_id: The flashcard group ID
            project_id: The project ID
            name: Optional new name
            description: Optional new description

        Returns:
            Updated FlashcardGroupDto

        Raises:
            NotFoundError: If flashcard group not found
        """
        with self._get_db_session() as db:
            try:
                flashcard_group = (
                    db.query(FlashcardGroup)
                    .filter(
                        FlashcardGroup.id == group_id,
                        FlashcardGroup.project_id == project_id,
                    )
                    .first()
                )
                if not flashcard_group:
                    raise NotFoundError(f"Flashcard group {group_id} not found")

                if name is not None:
                    flashcard_group.name = name
                if description is not None:
                    flashcard_group.description = description
                
                flashcard_group.updated_at = datetime.now()

                db.commit()
                db.refresh(flashcard_group)

                return self._model_to_dto(flashcard_group)
            except NotFoundError:
                raise
            except Exception as e:
                db.rollback()
                raise

    def delete_flashcard_group(self, group_id: str, project_id: str) -> None:
        """Delete a flashcard group.

        Args:
            group_id: The flashcard group ID
            project_id: The project ID

        Raises:
            NotFoundError: If flashcard group not found
        """
        with self._get_db_session() as db:
            try:
                flashcard_group = (
                    db.query(FlashcardGroup)
                    .filter(
                        FlashcardGroup.id == group_id,
                        FlashcardGroup.project_id == project_id,
                    )
                    .first()
                )
                if not flashcard_group:
                    raise NotFoundError(f"Flashcard group {group_id} not found")

                db.delete(flashcard_group)
                db.commit()
            except NotFoundError:
                raise
            except Exception as e:
                db.rollback()
                raise

    def _model_to_dto(self, flashcard_group: FlashcardGroup) -> FlashcardGroupDto:
        """Convert FlashcardGroup model to FlashcardGroupDto."""
        return FlashcardGroupDto(
            id=flashcard_group.id,
            project_id=flashcard_group.project_id,
            name=flashcard_group.name,
            description=flashcard_group.description,
            study_session_id=flashcard_group.study_session_id,
            created_at=flashcard_group.created_at,
            updated_at=flashcard_group.updated_at,
        )

    async def generate_and_populate(
        self,
        group_id: str,
        project_id: str,
        search_service: SearchService,
        agent_config: ContentAgentConfig,
        topic: Optional[str] = None,
        custom_instructions: Optional[str] = None,
    ) -> FlashcardGroupDto:
        """Generate flashcards using AI and populate an existing flashcard group.
        
        Args:
            group_id: The flashcard group ID to populate
            project_id: The project ID
            search_service: SearchService instance for RAG
            agent_config: ContentAgentConfig for AI generation
            topic: Optional topic for generation
            custom_instructions: Optional custom instructions
            
        Returns:
            Updated FlashcardGroupDto
            
        Raises:
            NotFoundError: If flashcard group not found
        """
        with self._get_db_session() as db:
            try:
                # Find existing flashcard group
                group = db.query(FlashcardGroup).filter(
                    FlashcardGroup.id == group_id,
                    FlashcardGroup.project_id == project_id,
                ).first()
                if not group:
                    raise NotFoundError(f"Flashcard group {group_id} not found")

                # Generate flashcards using AI
                flashcard_agent = FlashcardAgent(config=agent_config, search_service=search_service)
                result = await flashcard_agent.generate(
                    project_id=project_id,
                    topic=topic or "",
                    custom_instructions=custom_instructions,
                )

                # Update group with generated name and description
                group.name = result.name
                group.description = result.description
                group.updated_at = datetime.now()
                db.flush()

                # Delete existing flashcards and create new ones
                db.query(Flashcard).filter(Flashcard.group_id == group_id).delete()

                # Save flashcards to database
                for position, flashcard_item in enumerate(result.flashcards):
                    flashcard = Flashcard(
                        id=str(uuid4()),
                        group_id=group_id,
                        project_id=project_id,
                        question=flashcard_item.question,
                        answer=flashcard_item.answer,
                        difficulty_level=flashcard_item.difficulty_level,
                        position=position,
                        created_at=datetime.now(),
                    )
                    db.add(flashcard)

                db.commit()
                db.refresh(group)

                return self._model_to_dto(group)
            except NotFoundError:
                raise
            except Exception as e:
                db.rollback()
                raise

    def create_flashcard(
        self,
        group_id: str,
        project_id: str,
        question: str,
        answer: str,
        difficulty_level: str = "medium",
        position: Optional[int] = None,
    ) -> FlashcardDto:
        """Create a new flashcard in a group.

        Args:
            group_id: The flashcard group ID
            project_id: The project ID
            question: The flashcard question
            answer: The flashcard answer
            difficulty_level: The difficulty level (easy, medium, hard)
            position: Optional position for ordering (auto-assigned if None)

        Returns:
            Created FlashcardDto

        Raises:
            NotFoundError: If flashcard group not found
        """
        with self._get_db_session() as db:
            try:
                # Verify group exists
                group = (
                    db.query(FlashcardGroup)
                    .filter(
                        FlashcardGroup.id == group_id,
                        FlashcardGroup.project_id == project_id,
                    )
                    .first()
                )
                if not group:
                    raise NotFoundError(f"Flashcard group {group_id} not found")

                # Auto-assign position if not provided
                if position is None:
                    max_position = (
                        db.query(Flashcard.position)
                        .filter(Flashcard.group_id == group_id)
                        .order_by(Flashcard.position.desc())
                        .limit(1)
                        .scalar()
                    )
                    position = (max_position + 1) if max_position is not None else 0

                flashcard = Flashcard(
                    id=str(uuid4()),
                    group_id=group_id,
                    project_id=project_id,
                    question=question,
                    answer=answer,
                    difficulty_level=difficulty_level,
                    position=position,
                    created_at=datetime.now(),
                )
                db.add(flashcard)
                db.commit()
                db.refresh(flashcard)

                return self._flashcard_model_to_dto(flashcard)
            except NotFoundError:
                raise
            except Exception as e:
                db.rollback()
                raise

    def get_flashcard(
        self, flashcard_id: str, group_id: str, project_id: str
    ) -> FlashcardDto:
        """Get a flashcard by ID.

        Args:
            flashcard_id: The flashcard ID
            group_id: The flashcard group ID
            project_id: The project ID

        Returns:
            FlashcardDto

        Raises:
            NotFoundError: If flashcard not found
        """
        with self._get_db_session() as db:
            try:
                flashcard = (
                    db.query(Flashcard)
                    .filter(
                        Flashcard.id == flashcard_id,
                        Flashcard.group_id == group_id,
                        Flashcard.project_id == project_id,
                    )
                    .first()
                )
                if not flashcard:
                    raise NotFoundError(f"Flashcard {flashcard_id} not found")

                return self._flashcard_model_to_dto(flashcard)
            except NotFoundError:
                raise
            except Exception as e:
                raise

    def list_flashcards(
        self, group_id: str, project_id: str
    ) -> List[FlashcardDto]:
        """List all flashcards in a group.

        Args:
            group_id: The flashcard group ID
            project_id: The project ID

        Returns:
            List of FlashcardDto instances
        """
        with self._get_db_session() as db:
            try:
                flashcards = (
                    db.query(Flashcard)
                    .filter(
                        Flashcard.group_id == group_id,
                        Flashcard.project_id == project_id,
                    )
                    .order_by(Flashcard.position.asc())
                    .all()
                )
                return [self._flashcard_model_to_dto(flashcard) for flashcard in flashcards]
            except Exception as e:
                raise

    def update_flashcard(
        self,
        flashcard_id: str,
        group_id: str,
        project_id: str,
        question: Optional[str] = None,
        answer: Optional[str] = None,
        difficulty_level: Optional[str] = None,
        position: Optional[int] = None,
    ) -> FlashcardDto:
        """Update a flashcard.

        Args:
            flashcard_id: The flashcard ID
            group_id: The flashcard group ID
            project_id: The project ID
            question: Optional new question
            answer: Optional new answer
            difficulty_level: Optional new difficulty level
            position: Optional new position

        Returns:
            Updated FlashcardDto

        Raises:
            NotFoundError: If flashcard not found
        """
        with self._get_db_session() as db:
            try:
                flashcard = (
                    db.query(Flashcard)
                    .filter(
                        Flashcard.id == flashcard_id,
                        Flashcard.group_id == group_id,
                        Flashcard.project_id == project_id,
                    )
                    .first()
                )
                if not flashcard:
                    raise NotFoundError(f"Flashcard {flashcard_id} not found")

                if question is not None:
                    flashcard.question = question
                if answer is not None:
                    flashcard.answer = answer
                if difficulty_level is not None:
                    flashcard.difficulty_level = difficulty_level
                if position is not None:
                    flashcard.position = position

                db.commit()
                db.refresh(flashcard)

                return self._flashcard_model_to_dto(flashcard)
            except NotFoundError:
                raise
            except Exception as e:
                db.rollback()
                raise

    def delete_flashcard(
        self, flashcard_id: str, group_id: str, project_id: str
    ) -> None:
        """Delete a flashcard.

        Args:
            flashcard_id: The flashcard ID
            group_id: The flashcard group ID
            project_id: The project ID

        Raises:
            NotFoundError: If flashcard not found
        """
        with self._get_db_session() as db:
            try:
                flashcard = (
                    db.query(Flashcard)
                    .filter(
                        Flashcard.id == flashcard_id,
                        Flashcard.group_id == group_id,
                        Flashcard.project_id == project_id,
                    )
                    .first()
                )
                if not flashcard:
                    raise NotFoundError(f"Flashcard {flashcard_id} not found")

                db.delete(flashcard)
                db.commit()
            except NotFoundError:
                raise
            except Exception as e:
                db.rollback()
                raise

    def _flashcard_model_to_dto(self, flashcard: Flashcard) -> FlashcardDto:
        """Convert Flashcard model to FlashcardDto."""
        return FlashcardDto(
            id=flashcard.id,
            group_id=flashcard.group_id,
            project_id=flashcard.project_id,
            question=flashcard.question,
            answer=flashcard.answer,
            difficulty_level=flashcard.difficulty_level,
            position=flashcard.position,
            created_at=flashcard.created_at,
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

