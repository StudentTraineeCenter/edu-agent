from api.dependencies import get_adaptive_learning_service, get_user
from core.logger import get_logger
from core.services.adaptive_learning import AdaptiveLearningService
from db.models import User
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from schemas.adaptive_learning import (
    StudySessionProgressUpdate,
    StudySessionResponse,
)
from typing import List, Dict, Any, Optional

router = APIRouter()

logger = get_logger(__name__)


@router.post(
    "/projects/{project_id}/study-sessions/stream",
    status_code=status.HTTP_200_OK,
    summary="Generate adaptive study session with streaming progress",
    description="Generate a personalized study session with streaming progress updates",
)
async def generate_study_session_stream(
    project_id: str,
    session_length_minutes: int = Query(30, ge=10, le=120),
    focus_topics: Optional[List[str]] = Query(None),
    adaptive_service: AdaptiveLearningService = Depends(get_adaptive_learning_service),
    current_user: User = Depends(get_user),
):
    """Generate an adaptive study session with streaming progress updates."""

    async def generate_stream():
        """Generate streaming progress updates"""
        try:
            async for progress_update in adaptive_service.generate_study_session_stream(
                user_id=current_user.id,
                project_id=project_id,
                session_length_minutes=session_length_minutes,
                focus_topics=focus_topics,
            ):
                progress = StudySessionProgressUpdate(**progress_update)
                progress_json = progress.model_dump_json()
                sse_data = f"data: {progress_json}\n\n"
                yield sse_data.encode("utf-8")

        except Exception as e:
            logger.error_structured(
                "error in streaming study session generation",
                project_id=project_id,
                user_id=current_user.id,
                error=str(e),
                exc_info=True,
            )
            error_progress = StudySessionProgressUpdate(
                status="done",
                message="Error generating study session",
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
    "/projects/{project_id}/study-sessions",
    response_model=StudySessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate adaptive study session",
    description="Generate a personalized study session based on performance and spaced repetition",
)
async def generate_study_session(
    project_id: str,
    session_length_minutes: int = Query(30, ge=10, le=120),
    focus_topics: Optional[List[str]] = Query(None),
    adaptive_service: AdaptiveLearningService = Depends(get_adaptive_learning_service),
    current_user: User = Depends(get_user),
):
    """Generate an adaptive study session."""
    try:
        session = await adaptive_service.generate_study_session(
            user_id=current_user.id,
            project_id=project_id,
            session_length_minutes=session_length_minutes,
            focus_topics=focus_topics,
        )
        return StudySessionResponse(**session)
    except Exception as e:
        logger.error_structured("error generating study session", project_id=project_id, user_id=current_user.id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate study session",
        )


@router.get(
    "/projects/{project_id}/study-sessions",
    response_model=List[StudySessionResponse],
    status_code=status.HTTP_200_OK,
    summary="List study sessions",
    description="List all study sessions for a project",
)
async def list_study_sessions(
    project_id: str,
    limit: int = Query(50, ge=1, le=100),
    adaptive_service: AdaptiveLearningService = Depends(get_adaptive_learning_service),
    current_user: User = Depends(get_user),
):
    """List study sessions for a project."""
    try:
        sessions = adaptive_service.list_study_sessions(
            user_id=current_user.id, project_id=project_id, limit=limit
        )

        # Get flashcard group IDs for each session
        result = []
        for session in sessions:
            session_with_group = adaptive_service.get_study_session_with_group(
                session_id=session.id, user_id=current_user.id
            )
            flashcard_group_id = (
                session_with_group["flashcard_group_id"] if session_with_group else None
            )

            result.append(
                StudySessionResponse(
                    session_id=session.id,
                    flashcard_group_id=flashcard_group_id,
                    flashcards=session.session_data.get("flashcards", []),
                    estimated_time_minutes=session.estimated_time_minutes,
                    focus_topics=session.focus_topics or [],
                    learning_objectives=session.session_data.get(
                        "learning_objectives", []
                    ),
                    generated_at=session.generated_at.isoformat(),
                )
            )

        return result
    except Exception as e:
        logger.error_structured("error listing study sessions", project_id=project_id, user_id=current_user.id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list study sessions",
        )


@router.get(
    "/study-sessions/{session_id}",
    response_model=StudySessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get study session",
    description="Get a study session by ID",
)
async def get_study_session(
    session_id: str,
    adaptive_service: AdaptiveLearningService = Depends(get_adaptive_learning_service),
    current_user: User = Depends(get_user),
):
    """Get a study session by ID."""
    try:
        session = adaptive_service.get_study_session(
            session_id=session_id, user_id=current_user.id
        )
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Study session not found"
            )

        # Get the associated flashcard group
        session_with_group = adaptive_service.get_study_session_with_group(
            session_id=session_id, user_id=current_user.id
        )
        if not session_with_group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Study session not found"
            )

        session = session_with_group["session"]

        return StudySessionResponse(
            session_id=session.id,
            flashcard_group_id=session_with_group["flashcard_group_id"],
            flashcards=session.session_data.get("flashcards", []),
            estimated_time_minutes=session.estimated_time_minutes,
            focus_topics=session.focus_topics or [],
            learning_objectives=session.session_data.get("learning_objectives", []),
            generated_at=session.generated_at.isoformat(),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error_structured("error getting study session", session_id=session_id, user_id=current_user.id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get study session",
        )
