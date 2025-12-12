"""Router for note CRUD operations."""

from typing import AsyncGenerator, Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from auth import get_current_user
from config import get_settings
from edu_shared.services import NoteService, SearchService, NotFoundError
from edu_shared.agents.base import ContentAgentConfig
from edu_shared.schemas.notes import NoteDto
from edu_shared.schemas.users import UserDto
from routers.schemas import NoteCreate, NoteUpdate, GenerateRequest

router = APIRouter(prefix="/api/v1/projects/{project_id}/notes", tags=["notes"])


@router.post("", response_model=NoteDto, status_code=201)
async def create_note(
    project_id: str,
    note: NoteCreate,
    current_user: UserDto = Depends(get_current_user),
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
    current_user: UserDto = Depends(get_current_user),
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
    current_user: UserDto = Depends(get_current_user),
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
    current_user: UserDto = Depends(get_current_user),
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
    current_user: UserDto = Depends(get_current_user),
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


class GenerationProgressUpdate(BaseModel):
    """Progress update for generation streaming."""
    status: str = Field(..., description="Status: searching, generating, saving, done")
    message: str = Field(..., description="Progress message")
    error: Optional[str] = Field(None, description="Error message if any")


@router.post("/{note_id}/generate", response_model=NoteDto)
async def generate_note(
    project_id: str,
    note_id: str,
    request: GenerateRequest,
    current_user: UserDto = Depends(get_current_user),
):
    """Generate note content using AI and populate an existing note."""
    settings = get_settings()
    
    # Initialize SearchService for RAG
    search_service = SearchService(
        database_url=settings.database_url,
        azure_openai_embedding_deployment=settings.azure_openai_embedding_deployment,
        azure_openai_endpoint=settings.azure_openai_endpoint,
        azure_openai_api_version=settings.azure_openai_api_version,
    )
    
    # Create agent config
    agent_config = ContentAgentConfig(
        azure_openai_chat_deployment=settings.azure_openai_chat_deployment,
        azure_openai_endpoint=settings.azure_openai_endpoint,
        azure_openai_api_version=settings.azure_openai_api_version,
    )
    
    service = NoteService()
    try:
        return await service.generate_and_populate(
            note_id=note_id,
            project_id=project_id,
            search_service=search_service,
            agent_config=agent_config,
            topic=request.topic,
            custom_instructions=request.custom_instructions,
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
):
    """Generate note content using AI with streaming progress updates."""
    settings = get_settings()
    
    # Initialize SearchService for RAG
    search_service = SearchService(
        database_url=settings.database_url,
        azure_openai_embedding_deployment=settings.azure_openai_embedding_deployment,
        azure_openai_endpoint=settings.azure_openai_endpoint,
        azure_openai_api_version=settings.azure_openai_api_version,
    )
    
    # Create agent config
    agent_config = ContentAgentConfig(
        azure_openai_chat_deployment=settings.azure_openai_chat_deployment,
        azure_openai_endpoint=settings.azure_openai_endpoint,
        azure_openai_api_version=settings.azure_openai_api_version,
    )
    
    service = NoteService()
    
    async def generate_stream() -> AsyncGenerator[bytes, None]:
        """Generate streaming progress updates"""
        try:
            # Searching documents
            progress = GenerationProgressUpdate(
                status="searching",
                message="Searching relevant documents..."
            )
            yield f"data: {progress.model_dump_json()}\n\n".encode("utf-8")
            
            # Generate note content
            progress = GenerationProgressUpdate(
                status="generating",
                message="Generating note content with AI..."
            )
            yield f"data: {progress.model_dump_json()}\n\n".encode("utf-8")
            
            result = await service.generate_and_populate(
                note_id=note_id,
                project_id=project_id,
                search_service=search_service,
                agent_config=agent_config,
                topic=request.topic,
                custom_instructions=request.custom_instructions,
            )
            
            # Saving to database
            progress = GenerationProgressUpdate(
                status="saving",
                message="Saving note to database..."
            )
            yield f"data: {progress.model_dump_json()}\n\n".encode("utf-8")
            
            # Done
            progress = GenerationProgressUpdate(
                status="done",
                message="Successfully generated note content"
            )
            yield f"data: {progress.model_dump_json()}\n\n".encode("utf-8")
            
        except NotFoundError as e:
            error_progress = GenerationProgressUpdate(
                status="done",
                message="Error generating note content",
                error=str(e)
            )
            yield f"data: {error_progress.model_dump_json()}\n\n".encode("utf-8")
        except Exception as e:
            error_progress = GenerationProgressUpdate(
                status="done",
                message="Error generating note content",
                error=str(e)
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

