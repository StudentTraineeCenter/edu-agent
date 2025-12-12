"""Router for quiz CRUD operations."""

from fastapi import APIRouter, HTTPException

from edu_shared.services import QuizService, NotFoundError
from edu_shared.schemas.quizzes import QuizDto
from routers.schemas import QuizCreate, QuizUpdate

router = APIRouter(prefix="/api/v1/projects/{project_id}/quizzes", tags=["quizzes"])


@router.post("", response_model=QuizDto, status_code=201)
async def create_quiz(
    project_id: str,
    quiz: QuizCreate,
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

