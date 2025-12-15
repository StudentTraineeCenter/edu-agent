"""CRUD service for managing mind maps."""

from contextlib import contextmanager
from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from edu_db.models import MindMap
from edu_db.session import get_session_factory
from edu_core.exceptions import NotFoundError
from edu_core.schemas.mind_maps import MindMapDto

if TYPE_CHECKING:
    from edu_queue.service import QueueService


class MindMapService:
    """Service for managing mind maps."""

    def __init__(self, queue_service: "QueueService") -> None:
        """Initialize the mind map service.

        Args:
            queue_service: QueueService instance for async generation tasks
        """
        self.queue_service = queue_service

    def create_mind_map(
        self,
        user_id: str,
        project_id: str,
        title: str,
        description: str | None = None,
        map_data: dict[str, Any] | None = None,
    ) -> MindMapDto:
        """Create a new mind map.

        Args:
            user_id: The user ID
            project_id: The project ID
            title: The mind map title
            description: Optional description
            map_data: Optional map data (nodes, edges)

        Returns:
            Created MindMapDto
        """
        with self._get_db_session() as db:
            try:
                mind_map = MindMap(
                    id=str(uuid4()),
                    user_id=user_id,
                    project_id=project_id,
                    title=title,
                    description=description,
                    map_data=map_data or {"nodes": [], "edges": []},
                    generated_at=datetime.now(),
                    updated_at=datetime.now(),
                )
                db.add(mind_map)
                db.commit()
                db.refresh(mind_map)

                return self._model_to_dto(mind_map)
            except Exception:
                db.rollback()
                raise

    def get_mind_map(
        self, mind_map_id: str, project_id: str, user_id: str
    ) -> MindMapDto:
        """Get a mind map by ID.

        Args:
            mind_map_id: The mind map ID
            project_id: The project ID
            user_id: The user ID

        Returns:
            MindMapDto

        Raises:
            NotFoundError: If mind map not found
        """
        with self._get_db_session() as db:
            try:
                mind_map = (
                    db.query(MindMap)
                    .filter(
                        MindMap.id == mind_map_id,
                        MindMap.project_id == project_id,
                        MindMap.user_id == user_id,
                    )
                    .first()
                )
                if not mind_map:
                    raise NotFoundError(f"Mind map {mind_map_id} not found")

                return self._model_to_dto(mind_map)
            except NotFoundError:
                raise
            except Exception:
                raise

    def list_mind_maps(self, project_id: str, user_id: str) -> list[MindMapDto]:
        """List all mind maps for a project.

        Args:
            project_id: The project ID
            user_id: The user ID

        Returns:
            List of MindMapDto instances
        """
        with self._get_db_session() as db:
            try:
                mind_maps = (
                    db.query(MindMap)
                    .filter(
                        MindMap.project_id == project_id,
                        MindMap.user_id == user_id,
                    )
                    .order_by(MindMap.generated_at.desc())
                    .all()
                )
                return [self._model_to_dto(m) for m in mind_maps]
            except Exception:
                raise

    def _model_to_dto(self, mind_map: MindMap) -> MindMapDto:
        """Convert MindMap model to MindMapDto."""
        return MindMapDto(
            id=mind_map.id,
            user_id=mind_map.user_id,
            project_id=mind_map.project_id,
            title=mind_map.title,
            description=mind_map.description,
            map_data=mind_map.map_data,
            generated_at=mind_map.generated_at,
            updated_at=mind_map.updated_at,
        )

    def queue_generation(
        self,
        user_id: str,
        project_id: str,
        mind_map_id: str | None = None,
        topic: str | None = None,
        custom_instructions: str | None = None,
    ) -> MindMapDto:
        """Queue a mind map generation request to be processed by a worker.

        Args:
            user_id: The user ID
            project_id: The project ID
            queue_service: QueueService instance to send the message
            mind_map_id: Optional existing mind map ID to populate (if None, creates new)
            topic: Optional topic for generation
            custom_instructions: Optional custom instructions

        Returns:
            Existing or newly created MindMapDto (generation will happen asynchronously)

        Raises:
            NotFoundError: If mind_map_id is provided but mind map not found
        """
        from edu_queue.schemas import MindMapGenerationData, QueueTaskMessage, TaskType

        # If mind_map_id is provided, verify it exists
        if mind_map_id:
            mind_map = self.get_mind_map(
                mind_map_id=mind_map_id,
                project_id=project_id,
                user_id=user_id,
            )
        else:
            # Create a new empty mind map
            mind_map = self.create_mind_map(
                user_id=user_id,
                project_id=project_id,
                title="Generating...",
                description="Mind map is being generated",
                map_data={"nodes": [], "edges": []},
            )
            mind_map_id = mind_map.id

        # Prepare task data
        task_data: MindMapGenerationData = {
            "project_id": project_id,
            "user_id": user_id,
            "mind_map_id": mind_map_id,
        }
        if topic:
            task_data["topic"] = topic
        if custom_instructions:
            task_data["custom_instructions"] = custom_instructions

        # Send message to queue
        task_message: QueueTaskMessage = {
            "type": TaskType.MIND_MAP_GENERATION,
            "data": task_data,
        }
        self.queue_service.send_message(task_message)

        return mind_map

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
