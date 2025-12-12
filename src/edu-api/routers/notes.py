"""Router for note CRUD operations."""

from fastapi import APIRouter, HTTPException

from edu_shared.services import NoteService, NotFoundError
from edu_shared.schemas.notes import NoteDto
from routers.schemas import NoteCreate, NoteUpdate

router = APIRouter(prefix="/api/v1/projects/{project_id}/notes", tags=["notes"])


@router.post("", response_model=NoteDto, status_code=201)
async def create_note(
    project_id: str,
    note: NoteCreate,
):
    """Create a new note."""
    service = NoteService()
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
):
    """Get a note by ID."""
    service = NoteService()
    try:
        return service.get_note(note_id=note_id, project_id=project_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=list[NoteDto])
async def list_notes(
    project_id: str,
):
    """List all notes for a project."""
    service = NoteService()
    try:
        return service.list_notes(project_id=project_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{note_id}", response_model=NoteDto)
async def update_note(
    project_id: str,
    note_id: str,
    note: NoteUpdate,
):
    """Update a note."""
    service = NoteService()
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
):
    """Delete a note."""
    service = NoteService()
    try:
        service.delete_note(note_id=note_id, project_id=project_id)
        return None
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

