"""Router for quiz CRUD operations."""

from typing import AsyncGenerator, Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from auth import get_current_user
from config import get_settings
from edu_shared.services import QuizService, SearchService, NotFoundError
from edu_shared.agents.base import ContentAgentConfig
from edu_shared.schemas.quizzes import QuizDto
from edu_shared.schemas.users import UserDto
from routers.schemas import QuizCreate, QuizUpdate, GenerateRequest

router = APIRouter(prefix="/api/v1/projects/{project_id}/quizzes", tags=["quizzes"])


@router.post("", response_model=QuizDto, status_code=201)
async def create_quiz(
    project_id: str,
    quiz: QuizCreate,
    current_user: UserDto = Depends(get_current_user),
):
    """Create a new quiz."""
    service = QuizService()
    try:
        return service.create_quiz(
            project_id=project_id,
            name=quiz.name,
            description=quiz.description,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{quiz_id}", response_model=QuizDto)
async def get_quiz(
    project_id: str,
    quiz_id: str,
    current_user: UserDto = Depends(get_current_user),
):
    """Get a quiz by ID."""
    service = QuizService()
    try:
        return service.get_quiz(quiz_id=quiz_id, project_id=project_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=list[QuizDto])
async def list_quizzes(
    project_id: str,
    current_user: UserDto = Depends(get_current_user),
):
    """List all quizzes for a project."""
    service = QuizService()
    try:
        return service.list_quizzes(project_id=project_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{quiz_id}", response_model=QuizDto)
async def update_quiz(
    project_id: str,
    quiz_id: str,
    quiz: QuizUpdate,
    current_user: UserDto = Depends(get_current_user),
):
    """Update a quiz."""
    service = QuizService()
    try:
        return service.update_quiz(
            quiz_id=quiz_id,
            project_id=project_id,
            name=quiz.name,
            description=quiz.description,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{quiz_id}", status_code=204)
async def delete_quiz(
    project_id: str,
    quiz_id: str,
    current_user: UserDto = Depends(get_current_user),
):
    """Delete a quiz."""
    service = QuizService()
    try:
        service.delete_quiz(quiz_id=quiz_id, project_id=project_id)
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


@router.post("/{quiz_id}/generate", response_model=QuizDto)
async def generate_quiz(
    project_id: str,
    quiz_id: str,
    request: GenerateRequest,
    current_user: UserDto = Depends(get_current_user),
):
    """Generate quiz questions using AI and populate an existing quiz."""
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
    
    service = QuizService()
    try:
        return await service.generate_and_populate(
            quiz_id=quiz_id,
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


@router.post("/{quiz_id}/generate/stream", status_code=200)
async def generate_quiz_stream(
    project_id: str,
    quiz_id: str,
    request: GenerateRequest,
    current_user: UserDto = Depends(get_current_user),
):
    """Generate quiz questions using AI with streaming progress updates."""
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
    
    service = QuizService()
    
    async def generate_stream() -> AsyncGenerator[bytes, None]:
        """Generate streaming progress updates"""
        try:
            # Searching documents
            progress = GenerationProgressUpdate(
                status="searching",
                message="Searching relevant documents..."
            )
            yield f"data: {progress.model_dump_json()}\n\n".encode("utf-8")
            
            # Generate quiz questions
            progress = GenerationProgressUpdate(
                status="generating",
                message="Generating quiz questions with AI..."
            )
            yield f"data: {progress.model_dump_json()}\n\n".encode("utf-8")
            
            result = await service.generate_and_populate(
                quiz_id=quiz_id,
                project_id=project_id,
                search_service=search_service,
                agent_config=agent_config,
                topic=request.topic,
                custom_instructions=request.custom_instructions,
            )
            
            # Saving to database
            progress = GenerationProgressUpdate(
                status="saving",
                message="Saving quiz questions to database..."
            )
            yield f"data: {progress.model_dump_json()}\n\n".encode("utf-8")
            
            # Done
            progress = GenerationProgressUpdate(
                status="done",
                message="Successfully generated quiz questions"
            )
            yield f"data: {progress.model_dump_json()}\n\n".encode("utf-8")
            
        except NotFoundError as e:
            error_progress = GenerationProgressUpdate(
                status="done",
                message="Error generating quiz questions",
                error=str(e)
            )
            yield f"data: {error_progress.model_dump_json()}\n\n".encode("utf-8")
        except Exception as e:
            error_progress = GenerationProgressUpdate(
                status="done",
                message="Error generating quiz questions",
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

