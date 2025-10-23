from api.dependencies import get_quiz_service
from core.logger import get_logger
from core.services.quizzes import QuizService
from fastapi import APIRouter, Depends, HTTPException, Path, status
from schemas.quizzes import (
    CreateQuizRequest,
    QuizDto,
    QuizListResponse,
    QuizQuestionDto,
    QuizQuestionListResponse,
    QuizResponse,
    UpdateQuizRequest,
)

logger = get_logger(__name__)

router = APIRouter()


@router.post(
    path="",
    response_model=QuizResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a quiz",
    description="Create a new quiz for a project, optionally with generated questions",
)
async def create_quiz(
    project_id: str,
    request: CreateQuizRequest,
    quiz_service: QuizService = Depends(get_quiz_service),
):
    """Create a new quiz, optionally with generated questions."""
    try:
        logger.info("creating quiz for project_id=%s", project_id)

        quiz = await quiz_service.create_quiz_with_questions(
            project_id=project_id,
            count=request.question_count,
            user_prompt=request.user_prompt,
        )

        return QuizResponse(
            quiz=QuizDto(**quiz.__dict__), message="Quiz created successfully"
        )

    except ValueError as e:
        logger.error("validation error creating quiz: %s", e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error("error creating quiz: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create quiz",
        )


@router.get(
    path="",
    response_model=QuizListResponse,
    status_code=status.HTTP_200_OK,
    summary="List quizzes",
    description="List all quizzes for a project",
)
async def list_quizzes(
    project_id: str,
    quiz_service: QuizService = Depends(get_quiz_service),
):
    """List all quizzes for a project."""
    try:
        logger.info("listing quizzes for project_id=%s", project_id)

        quizzes = quiz_service.get_quizzes(project_id)

        return QuizListResponse(
            data=[QuizDto(**quiz.__dict__) for quiz in quizzes], total=len(quizzes)
        )

    except Exception as e:
        logger.error("error listing quizzes: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list quizzes",
        )


@router.get(
    path="/{quiz_id}",
    response_model=QuizResponse,
    status_code=status.HTTP_200_OK,
    summary="Get quiz",
    description="Get a specific quiz by ID",
)
async def get_quiz(
    quiz_id: str = Path(..., description="Quiz ID"),
    quiz_service: QuizService = Depends(get_quiz_service),
):
    """Get a specific quiz."""
    try:
        logger.info("getting quiz_id=%s", quiz_id)

        quiz = quiz_service.get_quiz(quiz_id)

        if not quiz:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found"
            )

        return QuizResponse(
            quiz=QuizDto(**quiz.__dict__), message="Quiz retrieved successfully"
        )

    except Exception as e:
        logger.error("error getting quiz: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get quiz",
        )


@router.put(
    path="/{quiz_id}",
    response_model=QuizResponse,
    status_code=status.HTTP_200_OK,
    summary="Update quiz",
    description="Update a quiz",
)
async def update_quiz(
    quiz_id: str = Path(..., description="Quiz ID"),
    request: UpdateQuizRequest = None,
    quiz_service: QuizService = Depends(get_quiz_service),
):
    """Update a quiz."""
    try:
        logger.info("updating quiz_id=%s", quiz_id)

        updated_quiz = quiz_service.update_quiz(
            quiz_id=quiz_id,
            name=request.name if request else None,
            description=request.description if request else None,
        )

        if not updated_quiz:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found"
            )

        return QuizResponse(
            quiz=QuizDto(**updated_quiz.__dict__), message="Quiz updated successfully"
        )

    except Exception as e:
        logger.error("error updating quiz: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update quiz",
        )


@router.delete(
    path="/{quiz_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete quiz",
    description="Delete a quiz and all its questions",
)
async def delete_quiz(
    quiz_id: str = Path(..., description="Quiz ID"),
    quiz_service: QuizService = Depends(get_quiz_service),
):
    """Delete a quiz."""
    try:
        logger.info("deleting quiz_id=%s", quiz_id)

        success = quiz_service.delete_quiz(quiz_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found"
            )

    except Exception as e:
        logger.error("error deleting quiz: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete quiz",
        )


@router.get(
    path="/{quiz_id}/questions",
    response_model=QuizQuestionListResponse,
    status_code=status.HTTP_200_OK,
    summary="List quiz questions",
    description="List all questions in a quiz",
)
async def list_quiz_questions(
    quiz_id: str = Path(..., description="Quiz ID"),
    quiz_service: QuizService = Depends(get_quiz_service),
):
    """List all questions in a quiz."""
    try:
        logger.info("listing quiz questions for quiz_id=%s", quiz_id)

        questions = quiz_service.get_quiz_questions(quiz_id)

        return QuizQuestionListResponse(
            quiz_questions=[
                QuizQuestionDto(**question.__dict__) for question in questions
            ],
            total=len(questions),
        )

    except Exception as e:
        logger.error("error listing quiz questions: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list quiz questions",
        )
