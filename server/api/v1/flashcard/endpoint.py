from fastapi import APIRouter, status, HTTPException, Depends, Path
from typing import List

from api.v1.flashcard.schema import (
    CreateFlashcardGroupRequest,
    UpdateFlashcardGroupRequest,
    FlashcardGroupResponse,
    FlashcardGroupListResponse,
    FlashcardListResponse,
    FlashcardGroupDto,
    FlashcardDto,
)
from api.v1.deps import get_flashcard_service

from core.logger import get_logger
from core.service.flashcard_service import FlashcardService

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
):
    """Create a new flashcard group, optionally with generated flashcards."""
    try:
        logger.info(f"Creating flashcard group for project {project_id}")

        group = await flashcard_service.create_flashcard_group_with_flashcards(
            project_id=project_id,
            count=request.flashcard_count,
            user_prompt=request.user_prompt,
        )

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
        logger.error(f"Validation error creating flashcard group: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating flashcard group: {e}")
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
):
    """List all flashcard groups for a project."""
    try:
        logger.info(f"Listing flashcard groups for project {project_id}")

        groups = flashcard_service.get_flashcard_groups(project_id)

        return FlashcardGroupListResponse(
            flashcard_groups=[FlashcardGroupDto(**group.__dict__) for group in groups],
            total=len(groups),
        )

    except Exception as e:
        logger.error(f"Error listing flashcard groups: {e}")
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
):
    """Get a specific flashcard group."""
    try:
        logger.info(f"Getting flashcard group {group_id}")

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
        logger.error(f"Error getting flashcard group: {e}")
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
):
    """Update a flashcard group."""
    try:
        logger.info(f"Updating flashcard group {group_id}")

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
        logger.error(f"Error updating flashcard group: {e}")
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
):
    """Delete a flashcard group."""
    try:
        logger.info(f"Deleting flashcard group {group_id}")

        success = flashcard_service.delete_flashcard_group(group_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Flashcard group not found",
            )

    except Exception as e:
        logger.error(f"Error deleting flashcard group: {e}")
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
):
    """List all flashcards in a group."""
    try:
        logger.info(f"Listing flashcards for group {group_id}")

        flashcards = flashcard_service.get_flashcards_by_group(group_id)

        return FlashcardListResponse(
            flashcards=[FlashcardDto(**flashcard.__dict__) for flashcard in flashcards],
            total=len(flashcards),
        )

    except Exception as e:
        logger.error(f"Error listing flashcards: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list flashcards",
        )
