"""Router for flashcard group CRUD operations."""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional

from auth import get_current_user
from edu_shared.services import FlashcardGroupService, NotFoundError
from edu_shared.schemas.flashcards import FlashcardGroupDto
from edu_shared.schemas.users import UserDto
from routers.schemas import FlashcardGroupCreate, FlashcardGroupUpdate

router = APIRouter(prefix="/api/v1/projects/{project_id}/flashcard-groups", tags=["flashcard-groups"])


@router.post("", response_model=FlashcardGroupDto, status_code=201)
async def create_flashcard_group(
    project_id: str,
    group: FlashcardGroupCreate,
    current_user: UserDto = Depends(get_current_user),
):
    """Create a new flashcard group."""
    service = FlashcardGroupService()
    try:
        return service.create_flashcard_group(
            project_id=project_id,
            name=group.name,
            description=group.description,
            study_session_id=group.study_session_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{group_id}", response_model=FlashcardGroupDto)
async def get_flashcard_group(
    project_id: str,
    group_id: str,
    current_user: UserDto = Depends(get_current_user),
):
    """Get a flashcard group by ID."""
    service = FlashcardGroupService()
    try:
        return service.get_flashcard_group(group_id=group_id, project_id=project_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=list[FlashcardGroupDto])
async def list_flashcard_groups(
    project_id: str,
    study_session_id: Optional[str] = Query(None, description="Filter by study session ID"),
    current_user: UserDto = Depends(get_current_user),
):
    """List all flashcard groups for a project."""
    service = FlashcardGroupService()
    try:
        return service.list_flashcard_groups(
            project_id=project_id,
            study_session_id=study_session_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{group_id}", response_model=FlashcardGroupDto)
async def update_flashcard_group(
    project_id: str,
    group_id: str,
    group: FlashcardGroupUpdate,
    current_user: UserDto = Depends(get_current_user),
):
    """Update a flashcard group."""
    service = FlashcardGroupService()
    try:
        return service.update_flashcard_group(
            group_id=group_id,
            project_id=project_id,
            name=group.name,
            description=group.description,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{group_id}", status_code=204)
async def delete_flashcard_group(
    project_id: str,
    group_id: str,
    current_user: UserDto = Depends(get_current_user),
):
    """Delete a flashcard group."""
    service = FlashcardGroupService()
    try:
        service.delete_flashcard_group(group_id=group_id, project_id=project_id)
        return None
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

