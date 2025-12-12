"""Router for flashcard group CRUD operations."""

from typing import AsyncGenerator, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from auth import get_current_user
from dependencies import (
    get_flashcard_group_service,
    get_search_service,
    get_content_agent_config,
)
from edu_shared.agents.base import ContentAgentConfig
from edu_shared.services import FlashcardGroupService, NotFoundError, SearchService
from edu_shared.schemas.flashcards import FlashcardGroupDto, FlashcardDto
from edu_shared.schemas.users import UserDto
from routers.schemas import FlashcardGroupCreate, FlashcardGroupUpdate, FlashcardCreate, FlashcardUpdate, GenerateRequest

router = APIRouter(prefix="/api/v1/projects/{project_id}/flashcard-groups", tags=["flashcard-groups"])


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
    study_session_id: Optional[str] = Query(None, description="Filter by study session ID"),
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
    error: Optional[str] = Field(None, description="Error message if any")


@router.post("/{group_id}/generate", response_model=FlashcardGroupDto)
async def generate_flashcards(
    project_id: str,
    group_id: str,
    request: GenerateRequest,
    current_user: UserDto = Depends(get_current_user),
    service: FlashcardGroupService = Depends(get_flashcard_group_service),
    search_service: SearchService = Depends(get_search_service),
    agent_config: ContentAgentConfig = Depends(get_content_agent_config),
):
    """Generate flashcards using AI and populate an existing flashcard group."""
    try:
        return await service.generate_and_populate(
            group_id=group_id,
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


@router.post("/{group_id}/generate/stream", status_code=200)
async def generate_flashcards_stream(
    project_id: str,
    group_id: str,
    request: GenerateRequest,
    current_user: UserDto = Depends(get_current_user),
    service: FlashcardGroupService = Depends(get_flashcard_group_service),
    search_service: SearchService = Depends(get_search_service),
    agent_config: ContentAgentConfig = Depends(get_content_agent_config),
):
    """Generate flashcards using AI with streaming progress updates."""
    
    async def generate_stream() -> AsyncGenerator[bytes, None]:
        """Generate streaming progress updates"""
        try:
            # Searching documents
            progress = GenerationProgressUpdate(
                status="searching",
                message="Searching relevant documents..."
            )
            yield f"data: {progress.model_dump_json()}\n\n".encode("utf-8")
            
            # Generate flashcards
            progress = GenerationProgressUpdate(
                status="generating",
                message="Generating flashcards with AI..."
            )
            yield f"data: {progress.model_dump_json()}\n\n".encode("utf-8")
            
            result = await service.generate_and_populate(
                group_id=group_id,
                project_id=project_id,
                search_service=search_service,
                agent_config=agent_config,
                topic=request.topic,
                custom_instructions=request.custom_instructions,
            )
            
            # Saving to database
            progress = GenerationProgressUpdate(
                status="saving",
                message="Saving flashcards to database..."
            )
            yield f"data: {progress.model_dump_json()}\n\n".encode("utf-8")
            
            # Done
            progress = GenerationProgressUpdate(
                status="done",
                message="Successfully generated flashcards"
            )
            yield f"data: {progress.model_dump_json()}\n\n".encode("utf-8")
            
        except NotFoundError as e:
            error_progress = GenerationProgressUpdate(
                status="done",
                message="Error generating flashcards",
                error=str(e)
            )
            yield f"data: {error_progress.model_dump_json()}\n\n".encode("utf-8")
        except Exception as e:
            error_progress = GenerationProgressUpdate(
                status="done",
                message="Error generating flashcards",
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

