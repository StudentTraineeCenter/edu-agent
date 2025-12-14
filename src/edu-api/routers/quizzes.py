"""Router for quiz CRUD operations."""

from typing import AsyncGenerator, Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from auth import get_current_user
from dependencies import (
    get_quiz_service,
    get_search_service,
    get_content_agent_config,
    get_usage_service,
    get_queue_service,
)
from edu_shared.services.queue import QueueService
from edu_shared.agents.base import ContentAgentConfig
from edu_shared.services import NotFoundError, QuizService, SearchService, UsageService
from edu_shared.schemas.quizzes import QuizDto, QuizQuestionDto
from edu_shared.schemas.users import UserDto
from routers.schemas import (
    QuizCreate,
    QuizUpdate,
    QuizQuestionCreate,
    QuizQuestionUpdate,
    QuizQuestionReorder,
    GenerateRequest,
)

router = APIRouter(prefix="/api/v1/projects/{project_id}/quizzes", tags=["quizzes"])


@router.post("", response_model=QuizDto, status_code=201)
async def create_quiz(
    project_id: str,
    quiz: QuizCreate,
    current_user: UserDto = Depends(get_current_user),
    service: QuizService = Depends(get_quiz_service),
):
    """Create a new quiz."""
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
    service: QuizService = Depends(get_quiz_service),
):
    """Get a quiz by ID."""
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
    service: QuizService = Depends(get_quiz_service),
):
    """List all quizzes for a project."""
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
    service: QuizService = Depends(get_quiz_service),
):
    """Update a quiz."""
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
    service: QuizService = Depends(get_quiz_service),
):
    """Delete a quiz."""
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
    service: QuizService = Depends(get_quiz_service),
    queue_service: QueueService = Depends(get_queue_service),
    usage_service: UsageService = Depends(get_usage_service),
):
    """Queue quiz generation request to be processed by a worker."""
    # Check usage limit before processing
    usage_service.check_and_increment(current_user.id, "quiz_generation")
    try:
        return service.queue_generation(
            quiz_id=quiz_id,
            project_id=project_id,
            queue_service=queue_service,
            topic=request.topic,
            custom_instructions=request.custom_instructions,
            user_id=current_user.id,
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
    service: QuizService = Depends(get_quiz_service),
    queue_service: QueueService = Depends(get_queue_service),
    usage_service: UsageService = Depends(get_usage_service),
):
    """Queue quiz generation request with streaming progress updates."""
    # Check usage limit before processing
    usage_service.check_and_increment(current_user.id, "quiz_generation")
    
    async def generate_stream() -> AsyncGenerator[bytes, None]:
        """Generate streaming progress updates"""
        try:
            # Queuing request
            progress = GenerationProgressUpdate(
                status="queuing",
                message="Queuing quiz generation request..."
            )
            yield f"data: {progress.model_dump_json()}\n\n".encode("utf-8")
            
            result = service.queue_generation(
                quiz_id=quiz_id,
                project_id=project_id,
                queue_service=queue_service,
                topic=request.topic,
                custom_instructions=request.custom_instructions,
                user_id=current_user.id,
            )
            
            # Done (queued)
            progress = GenerationProgressUpdate(
                status="done",
                message="Quiz generation request queued successfully"
            )
            yield f"data: {progress.model_dump_json()}\n\n".encode("utf-8")
            
        except NotFoundError as e:
            error_progress = GenerationProgressUpdate(
                status="done",
                message="Error queuing quiz generation",
                error=str(e)
            )
            yield f"data: {error_progress.model_dump_json()}\n\n".encode("utf-8")
        except Exception as e:
            error_progress = GenerationProgressUpdate(
                status="done",
                message="Error queuing quiz generation",
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


@router.get("/{quiz_id}/questions", response_model=list[QuizQuestionDto])
async def list_quiz_questions(
    project_id: str,
    quiz_id: str,
    current_user: UserDto = Depends(get_current_user),
    service: QuizService = Depends(get_quiz_service),
):
    """List all questions in a quiz."""
    try:
        return service.list_quiz_questions(quiz_id=quiz_id, project_id=project_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{quiz_id}/questions", response_model=QuizQuestionDto, status_code=201)
async def create_quiz_question(
    project_id: str,
    quiz_id: str,
    question: QuizQuestionCreate,
    current_user: UserDto = Depends(get_current_user),
    service: QuizService = Depends(get_quiz_service),
):
    """Create a new question in a quiz."""
    try:
        return service.create_quiz_question(
            quiz_id=quiz_id,
            project_id=project_id,
            question_text=question.question_text,
            option_a=question.option_a,
            option_b=question.option_b,
            option_c=question.option_c,
            option_d=question.option_d,
            correct_option=question.correct_option,
            explanation=question.explanation,
            difficulty_level=question.difficulty_level,
            position=question.position,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{quiz_id}/questions/{question_id}", response_model=QuizQuestionDto)
async def get_quiz_question(
    project_id: str,
    quiz_id: str,
    question_id: str,
    current_user: UserDto = Depends(get_current_user),
    service: QuizService = Depends(get_quiz_service),
):
    """Get a question by ID."""
    try:
        return service.get_quiz_question(
            question_id=question_id,
            quiz_id=quiz_id,
            project_id=project_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{quiz_id}/questions/{question_id}", response_model=QuizQuestionDto)
async def update_quiz_question(
    project_id: str,
    quiz_id: str,
    question_id: str,
    question: QuizQuestionUpdate,
    current_user: UserDto = Depends(get_current_user),
    service: QuizService = Depends(get_quiz_service),
):
    """Update a question."""
    try:
        return service.update_quiz_question(
            question_id=question_id,
            quiz_id=quiz_id,
            project_id=project_id,
            question_text=question.question_text,
            option_a=question.option_a,
            option_b=question.option_b,
            option_c=question.option_c,
            option_d=question.option_d,
            correct_option=question.correct_option,
            explanation=question.explanation,
            difficulty_level=question.difficulty_level,
            position=question.position,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{quiz_id}/questions/{question_id}", status_code=204)
async def delete_quiz_question(
    project_id: str,
    quiz_id: str,
    question_id: str,
    current_user: UserDto = Depends(get_current_user),
    service: QuizService = Depends(get_quiz_service),
):
    """Delete a question."""
    try:
        service.delete_quiz_question(
            question_id=question_id,
            quiz_id=quiz_id,
            project_id=project_id,
        )
        return None
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{quiz_id}/questions/reorder", response_model=list[QuizQuestionDto])
async def reorder_quiz_questions(
    project_id: str,
    quiz_id: str,
    reorder: QuizQuestionReorder,
    current_user: UserDto = Depends(get_current_user),
    service: QuizService = Depends(get_quiz_service),
):
    """Reorder questions in a quiz."""
    try:
        return service.reorder_quiz_questions(
            quiz_id=quiz_id,
            project_id=project_id,
            question_ids=reorder.question_ids,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

