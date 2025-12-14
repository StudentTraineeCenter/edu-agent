"""CRUD service for managing mind maps."""

from contextlib import contextmanager
from datetime import datetime
from typing import TYPE_CHECKING, Any, List, Optional
from uuid import uuid4

from edu_shared.agents.base import ContentAgentConfig
from edu_shared.agents.mind_map_agent import MindMapAgent
from langchain_openai import AzureChatOpenAI
from edu_shared.db.models import MindMap
from edu_shared.db.session import get_session_factory
from edu_shared.schemas.mind_maps import MindMapDto
from edu_shared.exceptions import NotFoundError
from edu_shared.services.search import SearchService
from edu_shared.db.models import Project

if TYPE_CHECKING:
    from edu_shared.services.queue import QueueService


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

    async def generate_mind_map(
        self,
        user_id: str,
        project_id: str,
        search_service: SearchService,
        llm: Optional[AzureChatOpenAI] = None,
        agent_config: Optional[ContentAgentConfig] = None,
        topic: Optional[str] = None,
        custom_instructions: Optional[str] = None,
    ) -> MindMapDto:
        """Generate a mind map using AI.
        
        Args:
            user_id: The user ID
            project_id: The project ID
            search_service: SearchService instance for RAG
            agent_config: ContentAgentConfig for AI generation
            topic: Optional topic for generation
            custom_instructions: Optional custom instructions
            
        Returns:
            Created MindMapDto
        """
        with self._get_db_session() as db:
            try:
                # Get project language code
                project = db.query(Project).filter(Project.id == project_id).first()
                language_code = getattr(project, "language_code", "en") if project else "en"

                # Generate mind map using AI
                mind_map_agent = MindMapAgent(
                    search_service=search_service,
                    llm=llm,
                    config=agent_config,
                )
                result = await mind_map_agent.generate(
                    project_id=project_id,
                    topic=topic or "",
                    custom_instructions=custom_instructions,
                    language_code=language_code,
                )

                # Convert agent result to map_data format
                map_data = {
                    "nodes": [
                        {
                            "id": node.id,
                            "data": {"label": node.label, **node.data},
                            "position": node.position,
                        }
                        for node in result.nodes
                    ],
                    "edges": [
                        {
                            "id": edge.id,
                            "source": edge.source,
                            "target": edge.target,
                            "label": edge.label,
                        }
                        for edge in result.edges
                    ],
                }

                # Create mind map
                mind_map = MindMap(
                    id=str(uuid4()),
                    user_id=user_id,
                    project_id=project_id,
                    title=result.title,
                    description=result.description,
                    map_data=map_data,
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

    async def generate_and_populate(
        self,
        mind_map_id: str,
        project_id: str,
        user_id: str,
        search_service: SearchService,
        llm: Optional[AzureChatOpenAI] = None,
        agent_config: Optional[ContentAgentConfig] = None,
        topic: Optional[str] = None,
        custom_instructions: Optional[str] = None,
    ) -> MindMapDto:
        """Generate mind map content using AI and populate an existing mind map.
        
        Args:
            mind_map_id: The mind map ID to populate
            project_id: The project ID
            user_id: The user ID
            search_service: SearchService instance for RAG
            agent_config: ContentAgentConfig for AI generation
            topic: Optional topic for generation
            custom_instructions: Optional custom instructions
            
        Returns:
            Updated MindMapDto
            
        Raises:
            NotFoundError: If mind map not found
        """
        with self._get_db_session() as db:
            try:
                # Find existing mind map
                mind_map = db.query(MindMap).filter(
                    MindMap.id == mind_map_id,
                    MindMap.project_id == project_id,
                    MindMap.user_id == user_id,
                ).first()
                if not mind_map:
                    raise NotFoundError(f"Mind map {mind_map_id} not found")

                # Get project language code
                project = db.query(Project).filter(Project.id == project_id).first()
                language_code = getattr(project, "language_code", "en") if project else "en"

                # Generate mind map using AI
                mind_map_agent = MindMapAgent(
                    search_service=search_service,
                    llm=llm,
                    config=agent_config,
                )
                result = await mind_map_agent.generate(
                    project_id=project_id,
                    topic=topic or "",
                    custom_instructions=custom_instructions,
                    language_code=language_code,
                )

                # Convert agent result to map_data format
                map_data = {
                    "nodes": [
                        {
                            "id": node.id,
                            "data": {"label": node.label, **node.data},
                            "position": node.position,
                        }
                        for node in result.nodes
                    ],
                    "edges": [
                        {
                            "id": edge.id,
                            "source": edge.source,
                            "target": edge.target,
                            "label": edge.label,
                        }
                        for edge in result.edges
                    ],
                }

                # Update mind map with generated content
                mind_map.title = result.title
                mind_map.description = result.description
                mind_map.map_data = map_data
                mind_map.updated_at = datetime.now()
                
                db.commit()
                db.refresh(mind_map)

                return self._model_to_dto(mind_map)
            except NotFoundError:
                raise
            except Exception as e:
                db.rollback()
                raise

    def queue_generation(
        self,
        user_id: str,
        project_id: str,
        queue_service: "QueueService",
        mind_map_id: Optional[str] = None,
        topic: Optional[str] = None,
        custom_instructions: Optional[str] = None,
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
        from edu_shared.schemas.queue import QueueTaskMessage, TaskType, MindMapGenerationData
        
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
        queue_service.send_message(task_message)
        
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

