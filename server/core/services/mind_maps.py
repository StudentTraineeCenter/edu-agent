"""Service for managing mind maps with AI generation capabilities."""

import uuid
from contextlib import contextmanager
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import AzureChatOpenAI
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from core.agents.prompts_utils import render_prompt
from core.agents.search import SearchInterface
from core.config import app_config
from core.logger import get_logger
from db.models import MindMap, Project
from db.session import SessionLocal

logger = get_logger(__name__)


class MindMapNode(BaseModel):
    """Represents a node in the mind map."""

    id: str = Field(description="Unique identifier for the node")
    label: str = Field(description="Text label for the node")
    position: Dict[str, float] = Field(
        description="Position coordinates {x, y} for the node"
    )
    data: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional data for the node"
    )


class MindMapEdge(BaseModel):
    """Represents an edge (connection) in the mind map."""

    id: str = Field(description="Unique identifier for the edge")
    source: str = Field(description="ID of the source node")
    target: str = Field(description="ID of the target node")
    label: Optional[str] = Field(
        default=None, description="Optional label for the edge"
    )


class MindMapGenerationRequest(BaseModel):
    """Pydantic model for mind map generation request."""

    title: str = Field(description="Title of the mind map")
    description: str = Field(description="Description of the mind map")
    nodes: List[MindMapNode] = Field(description="List of nodes in the mind map")
    edges: List[MindMapEdge] = Field(description="List of edges connecting nodes")


class MindMapGenerationResult(BaseModel):
    """Model for mind map generation result."""

    title: str
    description: str
    map_data: Dict[str, Any]


class MindMapService:
    """Service for managing mind maps with AI generation capabilities."""

    def __init__(self, search_interface: SearchInterface) -> None:
        """Initialize the mind map service.

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

        self.map_parser = JsonOutputParser(pydantic_object=MindMapGenerationRequest)

    async def generate_mind_map(
        self, user_id: str, project_id: str, custom_instructions: Optional[str] = None
    ) -> MindMap:
        """Generate a mind map from project documents.

        Args:
            user_id: The user's unique identifier
            project_id: The project ID
            custom_instructions: Optional custom instructions including topic, format preferences, and context

        Returns:
            Created MindMap model instance

        Raises:
            ValueError: If project not found or no documents available
        """
        with self._get_db_session() as db:
            try:
                logger.info(
                    f"generating mind map for user_id={user_id}, project_id={project_id}"
                )

                project = db.query(Project).filter(Project.id == project_id).first()
                if not project:
                    raise ValueError(f"Project {project_id} not found")

                language_code = project.language_code
                logger.info(
                    f"using language_code={language_code} for project_id={project_id}"
                )

                # Extract topic from custom_instructions if provided
                topic = None
                if custom_instructions:
                    topic = custom_instructions

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

                # Generate mind map using AI
                map_result = await self._generate_mind_map_content(
                    db=db,
                    project_id=project_id,
                    document_content=document_content,
                    custom_instructions=custom_instructions,
                    language_code=language_code,
                )

                # Create new mind map
                mind_map = MindMap(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    project_id=project_id,
                    title=map_result.title,
                    description=map_result.description,
                    map_data=map_result.map_data,
                    generated_at=datetime.now(),
                    updated_at=datetime.now(),
                )
                db.add(mind_map)
                db.commit()
                db.refresh(mind_map)
                logger.info_structured("created mind map", mind_map_id=mind_map.id, project_id=project_id)
                return mind_map

            except ValueError:
                raise
            except Exception as e:
                logger.error(
                    f"error generating mind map for user_id={user_id}, project_id={project_id}: {e}"
                )
                raise

    async def generate_mind_map_stream(
        self, user_id: str, project_id: str, custom_instructions: Optional[str] = None
    ) -> AsyncGenerator[dict, None]:
        """Generate a mind map with streaming progress updates.

        Args:
            user_id: The user's unique identifier
            project_id: The project ID
            custom_instructions: Optional custom instructions including topic, format preferences, and context

        Yields:
            Progress update dictionaries with status and message
        """
        try:
            yield {"status": "searching", "message": "Searching documents..."}

            with self._get_db_session() as db:
                project = db.query(Project).filter(Project.id == project_id).first()
                if not project:
                    yield {
                        "status": "done",
                        "message": "Error: Project not found",
                        "error": f"Project {project_id} not found",
                    }
                    return

                language_code = project.language_code

                # Extract topic from custom_instructions if provided
                topic = None
                if custom_instructions:
                    topic = custom_instructions

                yield {"status": "mapping", "message": "Mapping concepts..."}

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

                yield {"status": "building", "message": "Building connections..."}

                # Generate mind map using AI
                map_result = await self._generate_mind_map_content(
                    db=db,
                    project_id=project_id,
                    document_content=document_content,
                    custom_instructions=custom_instructions,
                    language_code=language_code,
                )

                # Create new mind map
                mind_map = MindMap(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    project_id=project_id,
                    title=map_result.title,
                    description=map_result.description,
                    map_data=map_result.map_data,
                    generated_at=datetime.now(),
                    updated_at=datetime.now(),
                )
                db.add(mind_map)
                db.commit()
                db.refresh(mind_map)
                logger.info_structured("created mind map", mind_map_id=mind_map.id, project_id=project_id)

                yield {
                    "status": "done",
                    "message": "Mind map created successfully",
                    "mind_map_id": str(mind_map.id),
                }

        except ValueError as e:
            logger.error_structured("error generating mind map", project_id=project_id, user_id=user_id, error=str(e))
            yield {
                "status": "done",
                "message": "Error creating mind map",
                "error": str(e),
            }
        except Exception as e:
            logger.error_structured("error generating mind map", project_id=project_id, user_id=user_id, error=str(e), exc_info=True)
            yield {
                "status": "done",
                "message": "Error creating mind map",
                "error": "Failed to create mind map. Please try again.",
            }

    def get_mind_map(self, mind_map_id: str, user_id: str) -> Optional[MindMap]:
        """Get a mind map by ID.

        Args:
            mind_map_id: The mind map ID
            user_id: The user's ID

        Returns:
            MindMap model instance or None if not found
        """
        with self._get_db_session() as db:
            try:
                mind_map = (
                    db.query(MindMap)
                    .filter(MindMap.id == mind_map_id, MindMap.user_id == user_id)
                    .first()
                )

                if mind_map:
                    logger.info_structured("retrieved mind map", mind_map_id=mind_map.id, user_id=user_id)
                else:
                    logger.info_structured("no mind map found", mind_map_id=mind_map_id, user_id=user_id)

                return mind_map
            except Exception as e:
                logger.error_structured("error retrieving mind map", mind_map_id=mind_map_id, user_id=user_id, error=str(e), exc_info=True)
                raise

    def list_mind_maps(self, project_id: str, user_id: str) -> List[MindMap]:
        """List all mind maps for a project.

        Args:
            project_id: The project ID
            user_id: The user's ID

        Returns:
            List of MindMap model instances
        """
        with self._get_db_session() as db:
            try:
                mind_maps = (
                    db.query(MindMap)
                    .filter(
                        MindMap.project_id == project_id, MindMap.user_id == user_id
                    )
                    .order_by(MindMap.generated_at.desc())
                    .all()
                )

                logger.info(
                    f"found {len(mind_maps)} mind maps for project_id={project_id}"
                )
                return mind_maps
            except Exception as e:
                logger.error(
                    f"error listing mind maps for project_id={project_id}: {e}"
                )
                raise

    async def _generate_mind_map_content(
        self,
        db: Session,
        project_id: str,
        document_content: str,
        custom_instructions: Optional[str],
        language_code: str,
    ) -> MindMapGenerationResult:
        """Generate mind map content from documents.

        Args:
            db: Database session
            project_id: The project ID
            document_content: Content from project documents
            custom_instructions: Optional custom instructions including topic, format preferences, and context
            language_code: Language code for the project

        Returns:
            MindMapGenerationResult containing title, description, and map data
        """
        try:
            logger.info_structured("generating mind map content", project_id=project_id, user_id=user_id)

            # Build the prompt using Jinja2 template
            prompt = render_prompt(
                "mind_map_prompt",
                document_content=document_content[
                    :12000
                ],  # Limit content to avoid token limits
                custom_instructions=custom_instructions
                or "Generate a comprehensive mind map covering key concepts, relationships, and important details.",
                language_code=language_code,
                format_instructions=self.map_parser.get_format_instructions(),
            )

            # Generate content
            response = await self.llm.ainvoke(prompt)

            # Parse the response
            parsed_dict = self.map_parser.parse(response.content)
            generation_request = MindMapGenerationRequest(**parsed_dict)

            # Convert to map_data format (compatible with ReactFlow)
            map_data = {
                "nodes": [
                    {
                        "id": node.id,
                        "type": "default",
                        "position": node.position,
                        "data": {"label": node.label, **(node.data or {})},
                    }
                    for node in generation_request.nodes
                ],
                "edges": [
                    {
                        "id": edge.id,
                        "source": edge.source,
                        "target": edge.target,
                        "label": edge.label,
                        "type": "smoothstep",
                    }
                    for edge in generation_request.edges
                ],
            }

            return MindMapGenerationResult(
                title=generation_request.title,
                description=generation_request.description,
                map_data=map_data,
            )
        except ValueError:
            raise
        except Exception as e:
            logger.error(
                f"error generating mind map content for project_id={project_id}: {e}"
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
