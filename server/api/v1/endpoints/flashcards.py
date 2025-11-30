from api.dependencies import get_flashcard_service, get_user
from core.logger import get_logger
from core.services.flashcards import FlashcardService
from db.models import User
from fastapi import APIRouter, Depends, HTTPException, Path, status
from schemas.flashcards import (
    CreateFlashcardGroupRequest,
    FlashcardDto,
    FlashcardGroupDto,
    FlashcardGroupListResponse,
    FlashcardGroupResponse,
    FlashcardListResponse,
)

logger = get_logger(__name__)

router = APIRouter()


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
