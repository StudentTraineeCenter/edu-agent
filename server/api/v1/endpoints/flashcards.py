from typing import Optional
from api.dependencies import (
    get_exporter_service,
    get_flashcard_service,
    get_flashcard_progress_service,
    get_user,
)
from core.logger import get_logger
from core.services.exporter import ExporterService
from core.services.flashcards import FlashcardService
from core.services.flashcard_progress import FlashcardProgressService
from db.models import User
from db.session import SessionLocal
from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, status
from fastapi.responses import Response, StreamingResponse
from schemas.flashcards import (
    CreateFlashcardGroupRequest,
    FlashcardDto,
    FlashcardGroupDto,
    FlashcardGroupListResponse,
    FlashcardGroupResponse,
    FlashcardListResponse,
    FlashcardProgressUpdate,
)

logger = get_logger(__name__)

router = APIRouter()


@router.post(
    path="/stream",
    status_code=status.HTTP_200_OK,
    summary="Create flashcard group with streaming progress",
    description="Create a new flashcard group with AI-generated flashcards and stream progress updates",
)
async def create_flashcard_group_stream(
    project_id: str,
    body: CreateFlashcardGroupRequest,
    flashcard_service: FlashcardService = Depends(get_flashcard_service),
    current_user: User = Depends(get_user),
):
    """Create a new flashcard group with streaming progress updates."""
    async def generate_stream():
        """Generate streaming progress updates"""
        try:
            async for progress_update in flashcard_service.create_flashcard_group_with_flashcards_stream(
                project_id=project_id,
                count=body.flashcard_count,
                user_prompt=body.user_prompt,
            ):
                progress = FlashcardProgressUpdate(**progress_update)
                progress_json = progress.model_dump_json()
                sse_data = f"data: {progress_json}\n\n"
                yield sse_data.encode("utf-8")

        except Exception as e:
            logger.error("error in streaming flashcard creation: %s", e, exc_info=True)
            error_progress = FlashcardProgressUpdate(
                status="done",
                message="Error creating flashcards",
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
    path="",
    response_model=FlashcardGroupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create flashcard group",
    description="Create a new flashcard group with AI-generated flashcards",
)
async def create_flashcard_group(
    project_id: str,
    body: CreateFlashcardGroupRequest,
    flashcard_service: FlashcardService = Depends(get_flashcard_service),
    current_user: User = Depends(get_user),
):
    """Create a new flashcard group."""
    try:
        logger.info("creating flashcard group for project_id=%s", project_id)

        group_id = await flashcard_service.create_flashcard_group_with_flashcards(
            project_id=project_id,
            count=body.flashcard_count,
            user_prompt=body.user_prompt,
        )

        group = flashcard_service.get_flashcard_group(group_id)

        if not group:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve created flashcard group",
            )

        return FlashcardGroupResponse(
            flashcard_group=FlashcardGroupDto(**group.__dict__),
            message="Flashcard group created successfully",
        )

    except ValueError as e:
        logger.error("error creating flashcard group: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error("error creating flashcard group: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create flashcard group",
        )


@router.get(
    path="",
    response_model=FlashcardGroupListResponse,
    status_code=status.HTTP_200_OK,
    summary="List flashcard groups",
    description="List all flashcard groups for a project",
)
async def list_flashcard_groups(
    project_id: str,
    flashcard_service: FlashcardService = Depends(get_flashcard_service),
    current_user: User = Depends(get_user),
):
    """List all flashcard groups for a project."""
    try:
        logger.info("listing flashcard groups for project_id=%s", project_id)

        groups = flashcard_service.get_flashcard_groups(project_id)

        return FlashcardGroupListResponse(
            data=[FlashcardGroupDto(**group.__dict__) for group in groups],
        )

    except Exception as e:
        logger.error("error listing flashcard groups: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list flashcard groups",
        )


@router.get(
    path="/{group_id}",
    response_model=FlashcardGroupResponse,
    status_code=status.HTTP_200_OK,
    summary="Get flashcard group",
    description="Get a specific flashcard group by ID",
)
async def get_flashcard_group(
    group_id: str = Path(..., description="Flashcard group ID"),
    flashcard_service: FlashcardService = Depends(get_flashcard_service),
    current_user: User = Depends(get_user),
):
    """Get a specific flashcard group."""
    try:
        logger.info("getting flashcard group_id=%s", group_id)

        group = flashcard_service.get_flashcard_group(group_id)

        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Flashcard group not found",
            )

        return FlashcardGroupResponse(
            flashcard_group=FlashcardGroupDto(**group.__dict__),
            message="Flashcard group retrieved successfully",
        )

    except Exception as e:
        logger.error("error getting flashcard group: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get flashcard group",
        )


@router.delete(
    path="/{group_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete flashcard group",
    description="Delete a flashcard group and all its flashcards",
)
async def delete_flashcard_group(
    group_id: str = Path(..., description="Flashcard group ID"),
    flashcard_service: FlashcardService = Depends(get_flashcard_service),
    current_user: User = Depends(get_user),
):
    """Delete a flashcard group."""
    try:
        logger.info("deleting flashcard group_id=%s", group_id)

        success = flashcard_service.delete_flashcard_group(group_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Flashcard group not found",
            )

    except Exception as e:
        logger.error("error deleting flashcard group: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete flashcard group",
        )


@router.get(
    path="/{group_id}/flashcards",
    response_model=FlashcardListResponse,
    status_code=status.HTTP_200_OK,
    summary="List flashcards",
    description="List all flashcards in a group",
)
async def list_flashcards(
    group_id: str = Path(..., description="Flashcard group ID"),
    flashcard_service: FlashcardService = Depends(get_flashcard_service),
    current_user: User = Depends(get_user),
):
    """List all flashcards in a group."""
    try:
        logger.info("listing flashcards for group_id=%s", group_id)

        flashcards = flashcard_service.get_flashcards_by_group(group_id)

        return FlashcardListResponse(
            data=[FlashcardDto(**flashcard.__dict__) for flashcard in flashcards],
        )

    except Exception as e:
        logger.error("error listing flashcards: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list flashcards",
        )


@router.get(
    path="/{group_id}/study-queue",
    response_model=FlashcardListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get flashcards for study queue",
    description="Get flashcards for study session. Returns un-mastered cards by default, with option to include mastered cards.",
)
async def get_study_queue(
    group_id: str = Path(..., description="Flashcard group ID"),
    include_mastered: bool = Query(
        False, description="Whether to include mastered cards"
    ),
    progress_service: FlashcardProgressService = Depends(
        get_flashcard_progress_service
    ),
    current_user: User = Depends(get_user),
):
    """Get flashcards for study queue."""
    try:
        logger.info(
            "getting study queue for group_id=%s, user_id=%s, include_mastered=%s",
            group_id,
            current_user.id,
            include_mastered,
        )

        db = SessionLocal()
        try:
            flashcards = progress_service.get_unmastered_flashcards(
                db=db,
                user_id=current_user.id,
                group_id=group_id,
                include_mastered=include_mastered,
            )
        finally:
            db.close()

        return FlashcardListResponse(
            data=[FlashcardDto(**flashcard.__dict__) for flashcard in flashcards],
        )

    except Exception as e:
        logger.error("error getting study queue: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get study queue",
        )


@router.get(
    path="/{group_id}/export",
    summary="Export flashcard group to CSV",
    description="Export a flashcard group to CSV format",
)
async def export_flashcard_group(
    group_id: str = Path(..., description="Flashcard group ID"),
    exporter_service: ExporterService = Depends(get_exporter_service),
    current_user: User = Depends(get_user),
):
    """Export flashcard group to CSV."""
    try:
        csv_content = exporter_service.export_flashcard_group_to_csv(group_id)
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=flashcards_{group_id}.csv"
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("error exporting flashcard group: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export flashcard group",
        )
