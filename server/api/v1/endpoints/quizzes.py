from api.dependencies import get_exporter_service, get_quiz_service, get_user
from core.logger import get_logger
from core.services.exporter import ExporterService
from core.services.quizzes import QuizService
from db.models import User
from fastapi import APIRouter, Depends, HTTPException, Path, status
from fastapi.responses import Response, StreamingResponse
from schemas.quizzes import (
    CreateQuizRequest,
    QuizDto,
    QuizListResponse,
    QuizProgressUpdate,
    QuizQuestionDto,
    QuizQuestionListResponse,
    QuizResponse,
)

logger = get_logger(__name__)

router = APIRouter()


@router.post(
    path="/stream",
    status_code=status.HTTP_200_OK,
    summary="Create quiz with streaming progress",
    description="Create a new quiz with AI-generated questions and stream progress updates",
)
async def create_quiz_stream(
    project_id: str,
    body: CreateQuizRequest,
    quiz_service: QuizService = Depends(get_quiz_service),
    current_user: User = Depends(get_user),
):
    """Create a new quiz with streaming progress updates."""
    import json

    async def generate_stream():
        """Generate streaming progress updates"""
        try:
            async for progress_update in quiz_service.create_quiz_with_questions_stream(
                project_id=project_id,
                count=body.question_count,
                user_prompt=body.user_prompt,
            ):
                progress = QuizProgressUpdate(**progress_update)
                progress_json = progress.model_dump_json()
                sse_data = f"data: {progress_json}\n\n"
                yield sse_data.encode("utf-8")

        except Exception as e:
            logger.error("error in streaming quiz creation: %s", e, exc_info=True)
            error_progress = QuizProgressUpdate(
                status="done",
                message="Error creating quiz",
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
    response_model=QuizResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create quiz",
    description="Create a new quiz with AI-generated questions",
)
async def create_quiz(
    project_id: str,
    body: CreateQuizRequest,
    quiz_service: QuizService = Depends(get_quiz_service),
    current_user: User = Depends(get_user),
):
    """Create a new quiz."""
    try:
        logger.info("creating quiz for project_id=%s", project_id)

        quiz_id = await quiz_service.create_quiz_with_questions(
            project_id=project_id,
            count=body.question_count,
            user_prompt=body.user_prompt,
        )

        quiz = quiz_service.get_quiz(quiz_id)

        if not quiz:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve created quiz",
            )

        return QuizResponse(
            quiz=QuizDto(**quiz.__dict__),
            message="Quiz created successfully",
        )

    except ValueError as e:
        logger.error("error creating quiz: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
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
            data=[QuizDto(**quiz.__dict__) for quiz in quizzes],
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
            data=[QuizQuestionDto(**question.__dict__) for question in questions],
        )

    except Exception as e:
        logger.error("error listing quiz questions: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list quiz questions",
        )


@router.get(
    path="/{quiz_id}/export",
    summary="Export quiz to CSV",
    description="Export a quiz to CSV format",
)
async def export_quiz(
    quiz_id: str = Path(..., description="Quiz ID"),
    exporter_service: ExporterService = Depends(get_exporter_service),
    current_user: User = Depends(get_user),
):
    """Export quiz to CSV."""
    try:
        csv_content = exporter_service.export_quiz_to_csv(quiz_id)
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=quiz_{quiz_id}.csv"},
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error("error exporting quiz: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export quiz",
        )
