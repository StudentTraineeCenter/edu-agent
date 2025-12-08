from api.dependencies import get_note_service, get_user
from core.logger import get_logger
from core.services.notes import NoteService
from db.models import User
from fastapi import APIRouter, Depends, HTTPException, Path, status
from fastapi.responses import StreamingResponse
from schemas.notes import (
    NoteDto,
    NoteListResponse,
    NoteProgressUpdate,
    NoteResponse,
    CreateNoteRequest,
    UpdateNoteRequest,
)

logger = get_logger(__name__)

router = APIRouter()


@router.post(
    path="/stream",
    status_code=status.HTTP_200_OK,
    summary="Create note with streaming progress",
    description="Create a new note with AI-generated markdown content and stream progress updates",
)
async def create_note_stream(
    project_id: str,
    body: CreateNoteRequest,
    note_service: NoteService = Depends(get_note_service),
    current_user: User = Depends(get_user),
):
    """Create a new note with streaming progress updates."""

    async def generate_stream():
        """Generate streaming progress updates"""
        try:
            async for progress_update in note_service.create_note_with_content_stream(
                project_id=project_id,
                user_prompt=body.user_prompt,
            ):
                progress = NoteProgressUpdate(**progress_update)
                progress_json = progress.model_dump_json()
                sse_data = f"data: {progress_json}\n\n"
                yield sse_data.encode("utf-8")

        except Exception as e:
            logger.error("error in streaming note creation: %s", e, exc_info=True)
            error_progress = NoteProgressUpdate(
                status="done",
                message="Error creating note",
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
    response_model=NoteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create note",
    description="Create a new note with AI-generated markdown content",
)
async def create_note(
    project_id: str,
    body: CreateNoteRequest,
    note_service: NoteService = Depends(get_note_service),
    current_user: User = Depends(get_user),
):
    """Create a new note."""
    try:
        logger.info("creating note for project_id=%s", project_id)

        note_id = await note_service.create_note_with_content(
            project_id=project_id,
            user_prompt=body.user_prompt,
        )

        note = note_service.get_note(note_id)

        if not note:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve created note",
            )

        return NoteResponse(
            note=NoteDto(**note.__dict__),
            message="Note created successfully",
        )

    except ValueError as e:
        logger.error("error creating note: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error("error creating note: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create note",
        )


@router.get(
    path="",
    response_model=NoteListResponse,
    status_code=status.HTTP_200_OK,
    summary="List notes",
    description="List all notes for a project",
)
async def list_notes(
    project_id: str,
    note_service: NoteService = Depends(get_note_service),
    current_user: User = Depends(get_user),
):
    """List all notes for a project."""
    try:
        logger.info("listing notes for project_id=%s", project_id)

        notes = note_service.get_notes(project_id)

        return NoteListResponse(
            data=[NoteDto(**note.__dict__) for note in notes],
        )

    except Exception as e:
        logger.error("error listing notes: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list notes",
        )


@router.get(
    path="/{note_id}",
    response_model=NoteResponse,
    status_code=status.HTTP_200_OK,
    summary="Get note",
    description="Get a specific note by ID",
)
async def get_note(
    note_id: str = Path(..., description="Note ID"),
    note_service: NoteService = Depends(get_note_service),
    current_user: User = Depends(get_user),
):
    """Get a specific note."""
    try:
        logger.info("getting note_id=%s", note_id)

        note = note_service.get_note(note_id)

        if not note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Note not found",
            )

        return NoteResponse(
            note=NoteDto(**note.__dict__),
            message="Note retrieved successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("error getting note: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get note",
        )


@router.put(
    path="/{note_id}",
    response_model=NoteResponse,
    status_code=status.HTTP_200_OK,
    summary="Update note",
    description="Update a note",
)
async def update_note(
    note_id: str = Path(..., description="Note ID"),
    body: UpdateNoteRequest = ...,
    note_service: NoteService = Depends(get_note_service),
    current_user: User = Depends(get_user),
):
    """Update a note."""
    try:
        logger.info("updating note_id=%s", note_id)

        note = note_service.update_note(
            note_id=note_id,
            title=body.title,
            description=body.description,
            content=body.content,
        )

        if not note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Note not found",
            )

        return NoteResponse(
            note=NoteDto(**note.__dict__),
            message="Note updated successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("error updating note: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update note",
        )


@router.delete(
    path="/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete note",
    description="Delete a note",
)
async def delete_note(
    note_id: str = Path(..., description="Note ID"),
    note_service: NoteService = Depends(get_note_service),
    current_user: User = Depends(get_user),
):
    """Delete a note."""
    try:
        logger.info("deleting note_id=%s", note_id)

        success = note_service.delete_note(note_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Note not found",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("error deleting note: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete note",
        )
