"""Service for managing mind maps with AI generation capabilities."""

import uuid
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import AzureChatOpenAI
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

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
        self, user_id: str, project_id: str, user_prompt: Optional[str] = None
    ) -> MindMap:
        """Generate a mind map from project documents.

        Args:
            user_id: The user's unique identifier
            project_id: The project ID
            user_prompt: Optional user instructions (topic or focus area)

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

                # Extract topic from user_prompt if provided
                topic = None
                if user_prompt:
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

                # Generate mind map using AI
                map_result = await self._generate_mind_map_content(
                    db=db,
                    project_id=project_id,
                    document_content=document_content,
                    user_prompt=user_prompt,
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
                logger.info(f"created mind map id={mind_map.id}")
                return mind_map

            except ValueError:
                raise
            except Exception as e:
                logger.error(
                    f"error generating mind map for user_id={user_id}, project_id={project_id}: {e}"
                )
                raise

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
                    logger.info(f"retrieved mind map id={mind_map.id}")
                else:
                    logger.info(f"no mind map found for id={mind_map_id}")

                return mind_map
            except Exception as e:
                logger.error(f"error retrieving mind map id={mind_map_id}: {e}")
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
        user_prompt: Optional[str],
        language_code: str,
    ) -> MindMapGenerationResult:
        """Generate mind map content from documents.

        Args:
            db: Database session
            project_id: The project ID
            document_content: Content from project documents
            user_prompt: Optional user instructions
            language_code: Language code for the project

        Returns:
            MindMapGenerationResult containing title, description, and map data
        """
        try:
            logger.info(f"generating mind map content for project_id={project_id}")

            # Create prompt template
            prompt_template = self._create_mind_map_prompt_template()

            # Build the prompt
            prompt = prompt_template.format(
                document_content=document_content[
                    :12000
                ],  # Limit content to avoid token limits
                user_prompt=user_prompt
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

    def _create_mind_map_prompt_template(self) -> PromptTemplate:
        """Create the prompt template for mind map generation.

        Returns:
            PromptTemplate instance
        """
        template = """You are an expert educational AI assistant specializing in creating mind maps from educational content. Your goal is to analyze document content and create a structured, hierarchical mind map that visualizes key concepts, relationships, and connections.

Document Content:
{document_content}

User Request: {user_prompt}

CRITICAL LANGUAGE REQUIREMENT: You MUST generate ALL content in {language_code} language. This includes:
- Mind map title and description
- All node labels
- All edge labels (if any)
- All text content
Never use any language other than {language_code}.

Guidelines for mind map creation:
1. Title: Generate a concise, descriptive title (3-8 words) in {language_code} that summarizes the main topic
2. Description: Generate a clear description (2-3 sentences) in {language_code} explaining what the mind map covers
3. Structure: Create a hierarchical structure with:
   - A central/root node (main topic)
   - Primary branches (major concepts, typically 3-7 nodes)
   - Secondary branches (sub-concepts, details)
   - Tertiary branches if needed (specific details, examples)
4. Nodes: Each node should have:
   - A unique ID (e.g., "node-1", "node-2", etc.)
   - A clear, concise label in {language_code} (1-5 words typically)
   - Position coordinates (x, y) - arrange in a radial or hierarchical layout
   - Optional data field for additional information
5. Edges: Connect related nodes with:
   - A unique ID (e.g., "edge-1", "edge-2", etc.)
   - Source and target node IDs
   - Optional label for the relationship type
6. Layout: Position nodes in a logical, readable layout:
   - Central node at approximately (0, 0) or center
   - Primary nodes arranged around the center (radial or hierarchical)
   - Secondary nodes positioned near their parent nodes
   - Use spacing: primary nodes ~200-300 units from center, secondary ~100-150 units from parent
7. Content Coverage: Ensure the mind map covers:
   - Main concepts and themes
   - Key definitions and terms
   - Important relationships and connections
   - Major categories or classifications
   - Critical details and examples
8. Balance: Create a balanced structure (not too sparse, not too dense)
   - Aim for 10-30 nodes total
   - 3-7 primary branches from center
   - 2-5 secondary nodes per primary branch
9. Clarity: Use clear, concise labels that are self-explanatory
10. Relationships: Show meaningful connections between related concepts

Position Guidelines:
- Center node: position around (0, 0) or (400, 300) for a 800x600 canvas
- Primary nodes: Position in a circle or semi-circle around center
  - For 4 nodes: positions like (0, -200), (200, 0), (0, 200), (-200, 0)
  - For 6 nodes: positions in a hexagon pattern
- Secondary nodes: Position near their parent, offset by ~150-200 units
- Use consistent spacing and avoid overlapping

{format_instructions}

Generate a comprehensive, well-structured mind map in {language_code} that visualizes the key concepts and relationships from the document content."""

        return PromptTemplate(
            template=template,
            input_variables=[
                "document_content",
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
