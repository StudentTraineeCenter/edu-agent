"""Service for managing mind maps with AI generation capabilities."""

import uuid
from contextlib import contextmanager
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import AzureChatOpenAI
from sqlalchemy.orm import Session

from core.agents.prompts_utils import render_prompt
from core.agents.search import SearchInterface
from core.config import app_config
from core.exceptions import BadRequestError, NotFoundError
from core.logger import get_logger
from db.models import MindMap, Project
from db.session import SessionLocal
from schemas.mind_maps import (
    MAX_DOCUMENT_CONTENT_LENGTH,
    MindMapEdge,
    MindMapGenerationRequest,
    MindMapGenerationResult,
    MindMapNode,
    MindMapProgressUpdate,
    SEARCH_TOP_K_WITH_TOPIC,
    SEARCH_TOP_K_WITHOUT_TOPIC,
)
from schemas.shared import (
    GenerationProgressUpdate,
    GenerationStatus,
)

logger = get_logger(__name__)


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
            NotFoundError: If project not found
            ValueError: If no documents available
        """
        with self._get_db_session() as db:
            try:
                logger.info_structured(
                    "generating mind map",
                    user_id=user_id,
                    project_id=project_id,
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

                map_result = await self._generate_mind_map_content(
                    db=db,
                    project_id=project_id,
                    document_content=document_content,
                    custom_instructions=custom_instructions,
                    language_code=language_code,
                )

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

                logger.info_structured(
                    "created mind map",
                    mind_map_id=mind_map.id,
                    project_id=project_id,
                    user_id=user_id,
                )
                return mind_map

            except (NotFoundError, ValueError, BadRequestError):
                raise
            except Exception as e:
                logger.error_structured(
                    "error generating mind map",
                    user_id=user_id,
                    project_id=project_id,
                    error=str(e),
                    exc_info=True,
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
                    status=GenerationStatus.MAPPING
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

                yield GenerationProgressUpdate(
                    status=GenerationStatus.BUILDING
                ).model_dump(exclude_none=True)

                language_code = project.language_code
                map_result = await self._generate_mind_map_content(
                    db=db,
                    project_id=project_id,
                    document_content=document_content,
                    custom_instructions=custom_instructions,
                    language_code=language_code,
                )

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

                logger.info_structured(
                    "created mind map",
                    mind_map_id=mind_map.id,
                    project_id=project_id,
                    user_id=user_id,
                )

                yield MindMapProgressUpdate(
                    status=GenerationStatus.DONE,
                    mind_map_id=str(mind_map.id),
                ).model_dump(exclude_none=True)

        except (NotFoundError, ValueError, BadRequestError) as e:
            logger.error_structured(
                "error generating mind map",
                project_id=project_id,
                user_id=user_id,
                error=str(e),
            )
            yield GenerationProgressUpdate(
                status=GenerationStatus.DONE,
                error=str(e),
            ).model_dump(exclude_none=True)
        except Exception as e:
            logger.error_structured(
                "error generating mind map",
                project_id=project_id,
                user_id=user_id,
                error=str(e),
                exc_info=True,
            )
            yield GenerationProgressUpdate(
                status=GenerationStatus.DONE,
                error="Failed to create mind map. Please try again.",
            ).model_dump(exclude_none=True)

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

                logger.info_structured(
                    "found mind maps",
                    count=len(mind_maps),
                    project_id=project_id,
                )
                return mind_maps
            except Exception as e:
                logger.error_structured(
                    "error listing mind maps",
                    project_id=project_id,
                    error=str(e),
                    exc_info=True,
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

        Raises:
            ValueError: If generation fails
        """
        try:
            logger.info_structured(
                "generating mind map content",
                project_id=project_id,
            )

            prompt = render_prompt(
                "mind_map_prompt",
                document_content=document_content[:MAX_DOCUMENT_CONTENT_LENGTH],
                custom_instructions=custom_instructions
                or "Generate a comprehensive mind map covering key concepts, relationships, and important details.",
                language_code=language_code,
                format_instructions=self.map_parser.get_format_instructions(),
            )

            response = await self.llm.ainvoke(prompt)
            parsed_dict = self.map_parser.parse(response.content)
            generation_request = MindMapGenerationRequest(**parsed_dict)

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
            logger.error_structured(
                "error generating mind map content",
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
