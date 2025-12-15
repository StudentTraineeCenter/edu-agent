"""Router for study session operations."""

from auth import get_current_user
from dependencies import get_study_session_service
from edu_core.exceptions import NotFoundError
from edu_core.schemas.study_sessions import StudySessionDto
from edu_core.schemas.users import UserDto
from edu_core.services import StudySessionService
from fastapi import APIRouter, Depends, HTTPException, Query

from routers.schemas import StudySessionCreate

router = APIRouter(
    prefix="/api/v1/projects/{project_id}/study-sessions", tags=["study-sessions"]
)
router_global = APIRouter(prefix="/api/v1/study-sessions", tags=["study-sessions"])


@router.get("", response_model=list[StudySessionDto])
async def list_study_sessions(
    project_id: str,
    limit: int = Query(
        50, ge=1, le=100, description="Maximum number of sessions to return"
    ),
    current_user: UserDto = Depends(get_current_user),
    service: StudySessionService = Depends(get_study_session_service),
):
    """List study sessions for a project."""
    try:
        return service.list_study_sessions(
            project_id=project_id,
            user_id=current_user.id,
            limit=limit,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router_global.get("/{session_id}", response_model=StudySessionDto)
async def get_study_session(
    session_id: str,
    current_user: UserDto = Depends(get_current_user),
    service: StudySessionService = Depends(get_study_session_service),
):
    """Get a study session by ID."""
    try:
        return service.get_study_session(
            session_id=session_id,
            user_id=current_user.id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=StudySessionDto, status_code=201)
async def create_study_session(
    project_id: str,
    request: StudySessionCreate,
    current_user: UserDto = Depends(get_current_user),
    service: StudySessionService = Depends(get_study_session_service),
):
    """Generate/create a study session.

    Note: AI generation is not yet implemented in edu-shared service.
    This endpoint creates a basic study session structure.
    """
    try:
        # For now, create a basic study session
        # TODO: Implement AI generation using adaptive learning service
        return service.create_study_session(
            user_id=current_user.id,
            project_id=project_id,
            session_length_minutes=request.session_length_minutes,
            focus_topics=request.focus_topics,
            session_data={
                "flashcards": [],
                "learning_objectives": [],
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
