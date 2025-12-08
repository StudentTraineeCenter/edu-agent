from api.dependencies import get_mind_map_service, get_user
from core.logger import get_logger
from core.services.mind_maps import MindMapService
from db.models import User
from fastapi import APIRouter, Depends, HTTPException, Path, status
from fastapi.responses import StreamingResponse
from schemas.mind_maps import (
    CreateMindMapRequest,
    MindMapDto,
    MindMapListResponse,
    MindMapProgressUpdate,
)

logger = get_logger(__name__)

router = APIRouter()


@router.post(
    "/projects/{project_id}/mind-maps/stream",
    status_code=status.HTTP_200_OK,
    summary="Generate mind map with streaming progress",
    description="Generate a new mind map from project documents with streaming progress updates",
)
async def generate_mind_map_stream(
    project_id: str = Path(..., description="Project ID"),
    body: CreateMindMapRequest = CreateMindMapRequest(),
    mind_map_service: MindMapService = Depends(get_mind_map_service),
    current_user: User = Depends(get_user),
):
    """Generate a new mind map with streaming progress updates."""

    async def generate_stream():
        """Generate streaming progress updates"""
        try:
            async for progress_update in mind_map_service.generate_mind_map_stream(
                user_id=current_user.id,
                project_id=project_id,
                user_prompt=body.user_prompt,
            ):
                progress = MindMapProgressUpdate(**progress_update)
                progress_json = progress.model_dump_json()
                sse_data = f"data: {progress_json}\n\n"
                yield sse_data.encode("utf-8")

        except Exception as e:
            logger.error("error in streaming mind map creation: %s", e, exc_info=True)
            error_progress = MindMapProgressUpdate(
                status="done",
                message="Error creating mind map",
                error=str(e),
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


@router.post(
    "/projects/{project_id}/mind-maps",
    response_model=MindMapDto,
    status_code=status.HTTP_201_CREATED,
    summary="Generate mind map",
    description="Generate a new mind map from project documents",
)
async def generate_mind_map(
    project_id: str = Path(..., description="Project ID"),
    body: CreateMindMapRequest = CreateMindMapRequest(),
    mind_map_service: MindMapService = Depends(get_mind_map_service),
    current_user: User = Depends(get_user),
):
    """Generate a new mind map from project documents."""
    try:
        logger.info(
            f"generating mind map for project_id={project_id}, user_id={current_user.id}"
        )

        mind_map = await mind_map_service.generate_mind_map(
            user_id=current_user.id,
            project_id=project_id,
            user_prompt=body.user_prompt,
        )

        return MindMapDto.model_validate(mind_map)
    except ValueError as e:
        logger.error(f"validation error generating mind map: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"error generating mind map: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate mind map",
        )


@router.get(
    "/projects/{project_id}/mind-maps",
    response_model=MindMapListResponse,
    status_code=status.HTTP_200_OK,
    summary="List mind maps",
    description="List all mind maps for a project",
)
async def list_mind_maps(
    project_id: str = Path(..., description="Project ID"),
    mind_map_service: MindMapService = Depends(get_mind_map_service),
    current_user: User = Depends(get_user),
):
    """List all mind maps for a project."""
    try:
        logger.info(
            f"listing mind maps for project_id={project_id}, user_id={current_user.id}"
        )

        mind_maps = mind_map_service.list_mind_maps(
            project_id=project_id,
            user_id=current_user.id,
        )

        return MindMapListResponse(
            data=[MindMapDto.model_validate(mind_map) for mind_map in mind_maps],
        )
    except Exception as e:
        logger.error(f"error listing mind maps: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list mind maps",
        )


@router.get(
    "/mind-maps/{mind_map_id}",
    response_model=MindMapDto,
    status_code=status.HTTP_200_OK,
    summary="Get mind map",
    description="Get a specific mind map by ID",
)
async def get_mind_map(
    mind_map_id: str = Path(..., description="Mind map ID"),
    mind_map_service: MindMapService = Depends(get_mind_map_service),
    current_user: User = Depends(get_user),
):
    """Get a specific mind map by ID."""
    try:
        logger.info(f"getting mind map id={mind_map_id}, user_id={current_user.id}")

        mind_map = mind_map_service.get_mind_map(
            mind_map_id=mind_map_id,
            user_id=current_user.id,
        )

        if not mind_map:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mind map not found",
            )

        return MindMapDto.model_validate(mind_map)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"error getting mind map: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get mind map",
        )
