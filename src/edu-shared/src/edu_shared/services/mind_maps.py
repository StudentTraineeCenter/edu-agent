"""CRUD service for managing mind maps."""

from contextlib import contextmanager
from datetime import datetime
from typing import Any, List, Optional
from uuid import uuid4

from edu_shared.db.models import MindMap
from edu_shared.db.session import get_session_factory
from edu_shared.schemas.mind_maps import MindMapDto
from edu_shared.exceptions import NotFoundError


class MindMapService:
    """Service for managing mind maps."""

    def __init__(self) -> None:
        """Initialize the mind map service."""
        pass

    def create_mind_map(
        self,
        user_id: str,
        project_id: str,
        title: str,
        description: Optional[str] = None,
        map_data: Optional[dict[str, Any]] = None,
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
            except Exception as e:
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
            except Exception as e:
                raise

    def list_mind_maps(
        self, project_id: str, user_id: str
    ) -> List[MindMapDto]:
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
            except Exception as e:
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

