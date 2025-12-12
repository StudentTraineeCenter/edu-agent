"""Router for mind map operations."""

from typing import AsyncGenerator, Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from auth import get_current_user
from dependencies import (
    get_mind_map_service,
    get_search_service,
    get_content_agent_config,
)
from edu_shared.agents.base import ContentAgentConfig
from edu_shared.services import NotFoundError, MindMapService, SearchService
from edu_shared.schemas.mind_maps import MindMapDto
from edu_shared.schemas.users import UserDto
from routers.schemas import MindMapCreate, GenerateRequest

router = APIRouter(prefix="/api/v1/projects/{project_id}/mind-maps", tags=["mind-maps"])


class GenerationProgressUpdate(BaseModel):
    """Progress update for generation streaming."""
    status: str = Field(..., description="Status: searching, generating, saving, done")
    message: str = Field(..., description="Progress message")
    error: Optional[str] = Field(None, description="Error message if any")


@router.get("", response_model=list[MindMapDto])
async def list_mind_maps(
    project_id: str,
    current_user: UserDto = Depends(get_current_user),
    service: MindMapService = Depends(get_mind_map_service),
):
    """List all mind maps for a project."""
    try:
        return service.list_mind_maps(
            project_id=project_id,
            user_id=current_user.id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{mind_map_id}", response_model=MindMapDto)
async def get_mind_map(
    project_id: str,
    mind_map_id: str,
    current_user: UserDto = Depends(get_current_user),
    service: MindMapService = Depends(get_mind_map_service),
):
    """Get a mind map by ID."""
    try:
        return service.get_mind_map(
            mind_map_id=mind_map_id,
            project_id=project_id,
            user_id=current_user.id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=MindMapDto, status_code=201)
async def create_mind_map(
    project_id: str,
    request: MindMapCreate,
    current_user: UserDto = Depends(get_current_user),
    service: MindMapService = Depends(get_mind_map_service),
):
    """Generate/create a mind map.
    
    Note: AI generation is not yet implemented in edu-shared service.
    This endpoint creates a basic mind map structure.
    """
    try:
        # For now, create a basic mind map
        # TODO: Implement AI generation using search_service and agent_config
        return service.create_mind_map(
            user_id=current_user.id,
            project_id=project_id,
            title=request.title,
            description=request.description,
            map_data={"nodes": [], "edges": []},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream", status_code=200)
async def create_mind_map_stream(
    project_id: str,
    request: MindMapCreate,
    current_user: UserDto = Depends(get_current_user),
    service: MindMapService = Depends(get_mind_map_service),
    search_service: SearchService = Depends(get_search_service),
    agent_config: ContentAgentConfig = Depends(get_content_agent_config),
):
    """Generate mind map with streaming progress updates.
    
    Note: AI generation is not yet implemented in edu-shared service.
    This endpoint provides a streaming interface but returns a basic structure.
    """
    
    async def generate_stream() -> AsyncGenerator[bytes, None]:
        """Generate streaming progress updates"""
        try:
            # Searching documents
            progress = GenerationProgressUpdate(
                status="searching",
                message="Searching relevant documents..."
            )
            yield f"data: {progress.model_dump_json()}\n\n".encode("utf-8")
            
            # Generating mind map
            progress = GenerationProgressUpdate(
                status="generating",
                message="Generating mind map with AI..."
            )
            yield f"data: {progress.model_dump_json()}\n\n".encode("utf-8")
            
            # TODO: Implement actual AI generation
            result = service.create_mind_map(
                user_id=current_user.id,
                project_id=project_id,
                title=request.title or "Generated Mind Map",
                description=request.description,
                map_data={"nodes": [], "edges": []},
            )
            
            # Saving to database
            progress = GenerationProgressUpdate(
                status="saving",
                message="Saving mind map to database..."
            )
            yield f"data: {progress.model_dump_json()}\n\n".encode("utf-8")
            
            # Done
            progress = GenerationProgressUpdate(
                status="done",
                message="Successfully generated mind map"
            )
            yield f"data: {progress.model_dump_json()}\n\n".encode("utf-8")
            
        except NotFoundError as e:
            error_progress = GenerationProgressUpdate(
                status="done",
                message="Error generating mind map",
                error=str(e)
            )
            yield f"data: {error_progress.model_dump_json()}\n\n".encode("utf-8")
        except Exception as e:
            error_progress = GenerationProgressUpdate(
                status="done",
                message="Error generating mind map",
                error=str(e)
            )
            yield f"data: {error_progress.model_dump_json()}\n\n".encode("utf-8")
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        },
    )

