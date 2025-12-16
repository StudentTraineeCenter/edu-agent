"""Router for flashcard group CRUD operations."""

from collections.abc import AsyncGenerator

from auth import get_current_user
from dependencies import (
    get_flashcard_group_service,
    get_usage_service,
)
from edu_core.exceptions import NotFoundError
from edu_core.schemas.flashcards import FlashcardDto, FlashcardGroupDto
from edu_core.schemas.users import UserDto
from edu_core.services import FlashcardGroupService, UsageService
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from routers.schemas import (
    FlashcardCreate,
    FlashcardGroupCreate,
    FlashcardGroupUpdate,
    FlashcardUpdate,
    GenerateRequest,
)

router = APIRouter(
    prefix="/api/v1/projects/{project_id}/flashcard-groups", tags=["flashcard-groups"]
)


@router.post("", response_model=FlashcardGroupDto, status_code=201)
async def create_flashcard_group(
    project_id: str,
    group: FlashcardGroupCreate,
    current_user: UserDto = Depends(get_current_user),
    service: FlashcardGroupService = Depends(get_flashcard_group_service),
):
    """Create a new flashcard group."""
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
    service: FlashcardGroupService = Depends(get_flashcard_group_service),
):
    """Get a flashcard group by ID."""
    try:
        return service.get_flashcard_group(group_id=group_id, project_id=project_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=list[FlashcardGroupDto])
async def list_flashcard_groups(
    project_id: str,
    study_session_id: str | None = Query(
        None, description="Filter by study session ID"
    ),
    current_user: UserDto = Depends(get_current_user),
    service: FlashcardGroupService = Depends(get_flashcard_group_service),
):
    """List all flashcard groups for a project."""
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
    service: FlashcardGroupService = Depends(get_flashcard_group_service),
):
    """Update a flashcard group."""
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
    service: FlashcardGroupService = Depends(get_flashcard_group_service),
):
    """Delete a flashcard group."""
    try:
        service.delete_flashcard_group(group_id=group_id, project_id=project_id)
        return None
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class GenerationProgressUpdate(BaseModel):
    """Progress update for generation streaming."""

    status: str = Field(..., description="Status: searching, generating, saving, done")
    message: str = Field(..., description="Progress message")
    error: str | None = Field(None, description="Error message if any")


@router.post("/{group_id}/generate", response_model=FlashcardGroupDto)
async def generate_flashcards(
    project_id: str,
    group_id: str,
    request: GenerateRequest,
    current_user: UserDto = Depends(get_current_user),
    service: FlashcardGroupService = Depends(get_flashcard_group_service),
    usage_service: UsageService = Depends(get_usage_service),
):
    """Queue flashcard generation request to be processed by a worker."""
    # Check usage limit before processing
    usage_service.check_and_increment(current_user.id, "flashcard_generation")
    try:
        return service.queue_generation(
            group_id=group_id,
            project_id=project_id,
            topic=request.topic,
            custom_instructions=request.custom_instructions,
            user_id=current_user.id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{group_id}/generate/stream", status_code=200)
async def generate_flashcards_stream(
    project_id: str,
    group_id: str,
    request: GenerateRequest,
    current_user: UserDto = Depends(get_current_user),
    service: FlashcardGroupService = Depends(get_flashcard_group_service),
    usage_service: UsageService = Depends(get_usage_service),
):
    """Queue flashcard generation request with streaming progress updates."""
    # Check usage limit before processing
    usage_service.check_and_increment(current_user.id, "flashcard_generation")

    async def generate_stream() -> AsyncGenerator[bytes]:
        """Generate streaming progress updates"""
        try:
            # Queuing request
            progress = GenerationProgressUpdate(
                status="queuing", message="Queuing flashcard generation request..."
            )
            yield f"data: {progress.model_dump_json()}\n\n".encode()

            service.queue_generation(
                group_id=group_id,
                project_id=project_id,
                topic=request.topic,
                custom_instructions=request.custom_instructions,
                user_id=current_user.id,
            )

            # Done (queued)
            progress = GenerationProgressUpdate(
                status="done",
                message="Flashcard generation request queued successfully",
            )
            yield f"data: {progress.model_dump_json()}\n\n".encode()

        except NotFoundError as e:
            error_progress = GenerationProgressUpdate(
                status="done",
                message="Error queuing flashcard generation",
                error=str(e),
            )
            yield f"data: {error_progress.model_dump_json()}\n\n".encode()
        except Exception as e:
            error_progress = GenerationProgressUpdate(
                status="done",
                message="Error queuing flashcard generation",
                error=str(e),
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


@router.post("/{group_id}/flashcards", response_model=FlashcardDto, status_code=201)
async def create_flashcard(
    project_id: str,
    group_id: str,
    flashcard: FlashcardCreate,
    current_user: UserDto = Depends(get_current_user),
    service: FlashcardGroupService = Depends(get_flashcard_group_service),
):
    """Create a new flashcard in a group."""
    try:
        return service.create_flashcard(
            group_id=group_id,
            project_id=project_id,
            question=flashcard.question,
            answer=flashcard.answer,
            difficulty_level=flashcard.difficulty_level,
            position=flashcard.position,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{group_id}/flashcards", response_model=list[FlashcardDto])
async def list_flashcards(
    project_id: str,
    group_id: str,
    current_user: UserDto = Depends(get_current_user),
    service: FlashcardGroupService = Depends(get_flashcard_group_service),
):
    """List all flashcards in a group."""
    try:
        return service.list_flashcards(group_id=group_id, project_id=project_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{group_id}/flashcards/{flashcard_id}", response_model=FlashcardDto)
async def get_flashcard(
    project_id: str,
    group_id: str,
    flashcard_id: str,
    current_user: UserDto = Depends(get_current_user),
    service: FlashcardGroupService = Depends(get_flashcard_group_service),
):
    """Get a flashcard by ID."""
    try:
        return service.get_flashcard(
            flashcard_id=flashcard_id,
            group_id=group_id,
            project_id=project_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{group_id}/flashcards/{flashcard_id}", response_model=FlashcardDto)
async def update_flashcard(
    project_id: str,
    group_id: str,
    flashcard_id: str,
    flashcard: FlashcardUpdate,
    current_user: UserDto = Depends(get_current_user),
    service: FlashcardGroupService = Depends(get_flashcard_group_service),
):
    """Update a flashcard."""
    try:
        return service.update_flashcard(
            flashcard_id=flashcard_id,
            group_id=group_id,
            project_id=project_id,
            question=flashcard.question,
            answer=flashcard.answer,
            difficulty_level=flashcard.difficulty_level,
            position=flashcard.position,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{group_id}/flashcards/{flashcard_id}", status_code=204)
async def delete_flashcard(
    project_id: str,
    group_id: str,
    flashcard_id: str,
    current_user: UserDto = Depends(get_current_user),
    service: FlashcardGroupService = Depends(get_flashcard_group_service),
):
    """Delete a flashcard."""
    try:
        service.delete_flashcard(
            flashcard_id=flashcard_id,
            group_id=group_id,
            project_id=project_id,
        )
        return None
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
