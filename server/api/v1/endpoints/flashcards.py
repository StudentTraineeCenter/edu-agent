from api.dependencies import get_flashcard_service, get_user, get_usage_service
from core.logger import get_logger
from core.services.flashcards import FlashcardService
from core.services.usage import UsageService
from db.models import User
from fastapi import APIRouter, Depends, HTTPException, Path, status
from schemas.flashcards import (
    CreateFlashcardGroupRequest,
    FlashcardDto,
    FlashcardGroupDto,
    FlashcardGroupListResponse,
    FlashcardGroupResponse,
    FlashcardListResponse,
    UpdateFlashcardGroupRequest,
)

logger = get_logger(__name__)

router = APIRouter()


@router.post(
    path="",
    response_model=FlashcardGroupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a flashcard group",
    description="Create a new flashcard group for a project, optionally with generated flashcards",
)
async def create_flashcard_group(
    project_id: str,
    request: CreateFlashcardGroupRequest,
    flashcard_service: FlashcardService = Depends(get_flashcard_service),
    current_user: User = Depends(get_user),
    usage_service: UsageService = Depends(get_usage_service),
):
    """Create a new flashcard group, optionally with generated flashcards."""
    try:
        # Check usage limit before processing
        usage_service.check_and_increment(current_user.id, "flashcard_generation")
        
        logger.info("creating flashcard group for project_id=%s", project_id)

        group_id = await flashcard_service.create_flashcard_group_with_flashcards(
            project_id=project_id,
            count=request.flashcard_count,
            user_prompt=request.user_prompt,
        )

        # Get the created group to return
        group = flashcard_service.get_flashcard_group(group_id)

        return FlashcardGroupResponse(
            flashcard_group=FlashcardGroupDto(
                id=group.id,
                project_id=group.project_id,
                name=group.name,
                description=group.description,
                created_at=group.created_at,
                updated_at=group.updated_at,
            ),
            message="Flashcard group created!",
        )

    except ValueError as e:
        logger.error("validation error creating flashcard group: %s", e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
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
            total=len(groups),
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


@router.put(
    path="/{group_id}",
    response_model=FlashcardGroupResponse,
    status_code=status.HTTP_200_OK,
    summary="Update flashcard group",
    description="Update a flashcard group",
)
async def update_flashcard_group(
    group_id: str = Path(..., description="Flashcard group ID"),
    request: UpdateFlashcardGroupRequest = None,
    flashcard_service: FlashcardService = Depends(get_flashcard_service),
    current_user: User = Depends(get_user),
):
    """Update a flashcard group."""
    try:
        logger.info("updating flashcard group_id=%s", group_id)

        updated_group = flashcard_service.update_flashcard_group(
            group_id=group_id,
            name=request.name if request else None,
            description=request.description if request else None,
        )

        if not updated_group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Flashcard group not found",
            )

        return FlashcardGroupResponse(
            flashcard_group=FlashcardGroupDto(**updated_group.__dict__),
            message="Flashcard group updated successfully",
        )

    except Exception as e:
        logger.error("error updating flashcard group: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update flashcard group",
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
            flashcards=[FlashcardDto(**flashcard.__dict__) for flashcard in flashcards],
            total=len(flashcards),
        )

    except Exception as e:
        logger.error("error listing flashcards: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list flashcards",
        )
