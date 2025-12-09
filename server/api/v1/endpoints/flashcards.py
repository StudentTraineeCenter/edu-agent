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
    CreateFlashcardRequest,
    FlashcardDto,
    FlashcardGroupDto,
    FlashcardGroupListResponse,
    FlashcardGroupResponse,
    FlashcardListResponse,
    FlashcardProgressUpdate,
    FlashcardResponse,
    ReorderFlashcardsRequest,
    UpdateFlashcardRequest,
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
            async for (
                progress_update
            ) in flashcard_service.create_flashcard_group_with_flashcards_stream(
                project_id=project_id,
                count=body.flashcard_count,
                custom_instructions=body.custom_instructions,
                length=body.length,
                difficulty=body.difficulty,
            ):
                progress = FlashcardProgressUpdate(**progress_update)
                progress_json = progress.model_dump_json()
                sse_data = f"data: {progress_json}\n\n"
                yield sse_data.encode("utf-8")

        except Exception as e:
            logger.error_structured("error in streaming flashcard creation", project_id=project_id, error=str(e), exc_info=True)
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
        logger.info_structured("creating flashcard group", project_id=project_id, user_id=current_user.id)

        group_id = await flashcard_service.create_flashcard_group_with_flashcards(
            project_id=project_id,
            count=body.flashcard_count,
            custom_instructions=body.custom_instructions,
            length=body.length,
            difficulty=body.difficulty,
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
        logger.error_structured("error creating flashcard group", project_id=project_id, user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error_structured("error creating flashcard group", project_id=project_id, user_id=current_user.id, error=str(e), exc_info=True)
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
        logger.info_structured("listing flashcard groups", project_id=project_id, user_id=current_user.id)

        groups = flashcard_service.get_flashcard_groups(project_id)

        return FlashcardGroupListResponse(
            data=[FlashcardGroupDto(**group.__dict__) for group in groups],
        )

    except Exception as e:
        logger.error_structured("error listing flashcard groups", project_id=project_id, user_id=current_user.id, error=str(e), exc_info=True)
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
        logger.info_structured("getting flashcard group", group_id=group_id, user_id=current_user.id)

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
        logger.error_structured("error getting flashcard group", group_id=group_id, user_id=current_user.id, error=str(e), exc_info=True)
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
        logger.info_structured("deleting flashcard group", group_id=group_id, user_id=current_user.id)

        success = flashcard_service.delete_flashcard_group(group_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Flashcard group not found",
            )

    except Exception as e:
        logger.error_structured("error deleting flashcard group", group_id=group_id, user_id=current_user.id, error=str(e), exc_info=True)
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
        logger.info_structured("listing flashcards", group_id=group_id, user_id=current_user.id)

        flashcards = flashcard_service.get_flashcards_by_group(group_id)

        return FlashcardListResponse(
            data=[FlashcardDto(**flashcard.__dict__) for flashcard in flashcards],
        )

    except Exception as e:
        logger.error_structured("error listing flashcards", group_id=group_id, user_id=current_user.id, error=str(e), exc_info=True)
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
        logger.info_structured(
            "getting study queue",
            group_id=group_id,
            user_id=current_user.id,
            include_mastered=include_mastered,
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
        logger.error_structured("error getting study queue", group_id=group_id, user_id=current_user.id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get study queue",
        )


@router.post(
    path="/{group_id}/flashcards",
    response_model=FlashcardResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create flashcard",
    description="Create a new flashcard in a group",
)
async def create_flashcard(
    group_id: str = Path(..., description="Flashcard group ID"),
    body: CreateFlashcardRequest = Body(...),
    flashcard_service: FlashcardService = Depends(get_flashcard_service),
    current_user: User = Depends(get_user),
):
    """Create a new flashcard."""
    try:
        logger.info_structured("creating flashcard", group_id=group_id, user_id=current_user.id)

        # Get group to get project_id
        group = flashcard_service.get_flashcard_group(group_id)
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Flashcard group not found",
            )

        flashcard = flashcard_service.create_flashcard(
            group_id=group_id,
            project_id=group.project_id,
            question=body.question,
            answer=body.answer,
            difficulty_level=body.difficulty_level,
            position=body.position,
        )

        return FlashcardResponse(
            flashcard=FlashcardDto(**flashcard.__dict__),
            message="Flashcard created successfully",
        )

    except ValueError as e:
        logger.error_structured("error creating flashcard", group_id=group_id, user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error_structured("error creating flashcard", group_id=group_id, user_id=current_user.id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create flashcard",
        )


@router.put(
    path="/flashcards/{flashcard_id}",
    response_model=FlashcardResponse,
    status_code=status.HTTP_200_OK,
    summary="Update flashcard",
    description="Update an existing flashcard",
)
async def update_flashcard(
    flashcard_id: str = Path(..., description="Flashcard ID"),
    body: UpdateFlashcardRequest = Body(...),
    flashcard_service: FlashcardService = Depends(get_flashcard_service),
    current_user: User = Depends(get_user),
):
    """Update an existing flashcard."""
    try:
        logger.info_structured("updating flashcard", flashcard_id=flashcard_id, user_id=current_user.id)

        flashcard = flashcard_service.update_flashcard(
            flashcard_id=flashcard_id,
            question=body.question,
            answer=body.answer,
            difficulty_level=body.difficulty_level,
        )

        if not flashcard:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Flashcard not found",
            )

        return FlashcardResponse(
            flashcard=FlashcardDto(**flashcard.__dict__),
            message="Flashcard updated successfully",
        )

    except Exception as e:
        logger.error_structured("error updating flashcard", flashcard_id=flashcard_id, user_id=current_user.id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update flashcard",
        )


@router.patch(
    path="/{group_id}/reorder",
    response_model=FlashcardListResponse,
    status_code=status.HTTP_200_OK,
    summary="Reorder flashcards",
    description="Reorder flashcards in a group",
)
async def reorder_flashcards(
    group_id: str = Path(..., description="Flashcard group ID"),
    body: ReorderFlashcardsRequest = Body(...),
    flashcard_service: FlashcardService = Depends(get_flashcard_service),
    current_user: User = Depends(get_user),
):
    """Reorder flashcards in a group."""
    try:
        logger.info_structured("reordering flashcards", group_id=group_id, user_id=current_user.id)

        flashcards = flashcard_service.reorder_flashcards(
            group_id=group_id,
            flashcard_ids=body.flashcard_ids,
        )

        return FlashcardListResponse(
            data=[FlashcardDto(**flashcard.__dict__) for flashcard in flashcards],
        )

    except ValueError as e:
        logger.error_structured("error reordering flashcards", group_id=group_id, user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error_structured("error reordering flashcards", group_id=group_id, user_id=current_user.id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reorder flashcards",
        )


@router.delete(
    path="/flashcards/{flashcard_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete flashcard",
    description="Delete a flashcard",
)
async def delete_flashcard(
    flashcard_id: str = Path(..., description="Flashcard ID"),
    flashcard_service: FlashcardService = Depends(get_flashcard_service),
    current_user: User = Depends(get_user),
):
    """Delete a flashcard."""
    try:
        logger.info_structured("deleting flashcard", flashcard_id=flashcard_id, user_id=current_user.id)

        success = flashcard_service.delete_flashcard(flashcard_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Flashcard not found",
            )

    except Exception as e:
        logger.error_structured("error deleting flashcard", flashcard_id=flashcard_id, user_id=current_user.id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete flashcard",
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
        logger.error_structured("error exporting flashcard group", group_id=group_id, user_id=current_user.id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export flashcard group",
        )
