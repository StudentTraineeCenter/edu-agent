"""Router for mind map operations."""

from collections.abc import AsyncGenerator

from auth import get_current_user
from dependencies import (
    get_mind_map_service,
    get_usage_service,
)
from edu_core.exceptions import NotFoundError
from edu_core.schemas.mind_maps import MindMapDto
from edu_core.schemas.users import UserDto
from edu_core.services import MindMapService, UsageService
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from routers.schemas import MindMapCreate

router = APIRouter(prefix="/api/v1/projects/{project_id}/mind-maps", tags=["mind-maps"])


class GenerationProgressUpdate(BaseModel):
    """Progress update for generation streaming."""

    status: str = Field(..., description="Status: searching, generating, saving, done")
    message: str = Field(..., description="Progress message")
    error: str | None = Field(None, description="Error message if any")


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
    usage_service: UsageService = Depends(get_usage_service),
):
    """Generate/create a mind map.

    Note: AI generation is not yet implemented in edu-shared service.
    This endpoint creates a basic mind map structure.
    """
    # Check usage limit before processing
    usage_service.check_and_increment(current_user.id, "mindmap_generation")

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
    usage_service: UsageService = Depends(get_usage_service),
):
    """Queue mind map generation request with streaming progress updates."""

    # Check usage limit before processing
    usage_service.check_and_increment(current_user.id, "mindmap_generation")

    async def generate_stream() -> AsyncGenerator[bytes]:
        """Generate streaming progress updates"""
        try:
            # Queuing request
            progress = GenerationProgressUpdate(
                status="queuing", message="Queuing mind map generation request..."
            )
            yield f"data: {progress.model_dump_json()}\n\n".encode()

            service.queue_generation(
                user_id=current_user.id,
                project_id=project_id,
                topic=request.title or request.custom_instructions or "",
                custom_instructions=request.custom_instructions or request.description,
            )

            # Done (queued)
            progress = GenerationProgressUpdate(
                status="done", message="Mind map generation request queued successfully"
            )
            yield f"data: {progress.model_dump_json()}\n\n".encode()

        except NotFoundError as e:
            error_progress = GenerationProgressUpdate(
                status="done", message="Error queuing mind map generation", error=str(e)
            )
            yield f"data: {error_progress.model_dump_json()}\n\n".encode()
        except Exception as e:
            error_progress = GenerationProgressUpdate(
                status="done", message="Error queuing mind map generation", error=str(e)
            )
            yield f"data: {error_progress.model_dump_json()}\n\n".encode()

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
