"""Router for note CRUD operations."""

from collections.abc import AsyncGenerator

from auth import get_current_user
from dependencies import (
    get_note_service,
)
from edu_shared.schemas.notes import NoteDto
from edu_shared.schemas.users import UserDto
from edu_shared.services import NoteService, NotFoundError
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from routers.schemas import GenerateRequest, NoteCreate, NoteUpdate

router = APIRouter(prefix="/api/v1/projects/{project_id}/notes", tags=["notes"])


@router.post("", response_model=NoteDto, status_code=201)
async def create_note(
    project_id: str,
    note: NoteCreate,
    current_user: UserDto = Depends(get_current_user),
    service: NoteService = Depends(get_note_service),
):
    """Create a new note."""
    try:
        return service.create_note(
            project_id=project_id,
            title=note.title,
            content=note.content,
            description=note.description,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{note_id}", response_model=NoteDto)
async def get_note(
    project_id: str,
    note_id: str,
    current_user: UserDto = Depends(get_current_user),
    service: NoteService = Depends(get_note_service),
):
    """Get a note by ID."""
    try:
        return service.get_note(note_id=note_id, project_id=project_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=list[NoteDto])
async def list_notes(
    project_id: str,
    current_user: UserDto = Depends(get_current_user),
    service: NoteService = Depends(get_note_service),
):
    """List all notes for a project."""
    try:
        return service.list_notes(project_id=project_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{note_id}", response_model=NoteDto)
async def update_note(
    project_id: str,
    note_id: str,
    note: NoteUpdate,
    current_user: UserDto = Depends(get_current_user),
    service: NoteService = Depends(get_note_service),
):
    """Update a note."""
    try:
        return service.update_note(
            note_id=note_id,
            project_id=project_id,
            title=note.title,
            description=note.description,
            content=note.content,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{note_id}", status_code=204)
async def delete_note(
    project_id: str,
    note_id: str,
    current_user: UserDto = Depends(get_current_user),
    service: NoteService = Depends(get_note_service),
):
    """Delete a note."""
    try:
        service.delete_note(note_id=note_id, project_id=project_id)
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


@router.post("/{note_id}/generate", response_model=NoteDto)
async def generate_note(
    project_id: str,
    note_id: str,
    request: GenerateRequest,
    current_user: UserDto = Depends(get_current_user),
    service: NoteService = Depends(get_note_service),
):
    """Queue note generation request to be processed by a worker."""
    try:
        return service.queue_generation(
            note_id=note_id,
            project_id=project_id,
            topic=request.topic,
            custom_instructions=request.custom_instructions,
            user_id=current_user.id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{note_id}/generate/stream", status_code=200)
async def generate_note_stream(
    project_id: str,
    note_id: str,
    request: GenerateRequest,
    current_user: UserDto = Depends(get_current_user),
    service: NoteService = Depends(get_note_service),
):
    """Queue note generation request with streaming progress updates."""

    async def generate_stream() -> AsyncGenerator[bytes]:
        """Generate streaming progress updates"""
        try:
            # Queuing request
            progress = GenerationProgressUpdate(
                status="queuing", message="Queuing note generation request..."
            )
            yield f"data: {progress.model_dump_json()}\n\n".encode()

            result = service.queue_generation(
                note_id=note_id,
                project_id=project_id,
                topic=request.topic,
                custom_instructions=request.custom_instructions,
                user_id=current_user.id,
            )

            # Done (queued)
            progress = GenerationProgressUpdate(
                status="done", message="Note generation request queued successfully"
            )
            yield f"data: {progress.model_dump_json()}\n\n".encode()

        except NotFoundError as e:
            error_progress = GenerationProgressUpdate(
                status="done", message="Error queuing note generation", error=str(e)
            )
            yield f"data: {error_progress.model_dump_json()}\n\n".encode()
        except Exception as e:
            error_progress = GenerationProgressUpdate(
                status="done", message="Error queuing note generation", error=str(e)
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
