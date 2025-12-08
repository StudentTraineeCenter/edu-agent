from api.dependencies import get_exporter_service, get_quiz_service, get_user
from core.logger import get_logger
from core.services.exporter import ExporterService
from core.services.quizzes import QuizService
from db.models import User
from fastapi import APIRouter, Body, Depends, HTTPException, Path, status
from fastapi.responses import Response, StreamingResponse
from schemas.quizzes import (
    CreateQuizRequest,
    CreateQuizQuestionRequest,
    QuizDto,
    QuizListResponse,
    QuizProgressUpdate,
    QuizQuestionDto,
    QuizQuestionListResponse,
    QuizQuestionResponse,
    QuizResponse,
    ReorderQuizQuestionsRequest,
    UpdateQuizQuestionRequest,
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
                length=body.length,
                difficulty=body.difficulty,
            ):
                progress = QuizProgressUpdate(**progress_update)
                progress_json = progress.model_dump_json()
                sse_data = f"data: {progress_json}\n\n"
                yield sse_data.encode("utf-8")

        except Exception as e:
            logger.error_structured("error in streaming quiz creation", project_id=project_id, user_id=current_user.id, error=str(e), exc_info=True)
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
        logger.info_structured("creating quiz", project_id=project_id, user_id=current_user.id)

        quiz_id = await quiz_service.create_quiz_with_questions(
            project_id=project_id,
            count=body.question_count,
            user_prompt=body.user_prompt,
            length=body.length,
            difficulty=body.difficulty,
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
        logger.error_structured("error creating quiz", project_id=project_id, user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error_structured("error creating quiz", project_id=project_id, user_id=current_user.id, error=str(e), exc_info=True)
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
        logger.info_structured("listing quizzes", project_id=project_id)

        quizzes = quiz_service.get_quizzes(project_id)

        return QuizListResponse(
            data=[QuizDto(**quiz.__dict__) for quiz in quizzes],
        )

    except Exception as e:
        logger.error_structured("error listing quizzes", project_id=project_id, error=str(e), exc_info=True)
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
        logger.info_structured("getting quiz", quiz_id=quiz_id)

        quiz = quiz_service.get_quiz(quiz_id)

        if not quiz:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found"
            )

        return QuizResponse(
            quiz=QuizDto(**quiz.__dict__), message="Quiz retrieved successfully"
        )

    except Exception as e:
        logger.error_structured("error getting quiz", quiz_id=quiz_id, error=str(e), exc_info=True)
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
        logger.info_structured("deleting quiz", quiz_id=quiz_id)

        success = quiz_service.delete_quiz(quiz_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Quiz not found"
            )

    except Exception as e:
        logger.error_structured("error deleting quiz", quiz_id=quiz_id, error=str(e), exc_info=True)
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
        logger.info_structured("listing quiz questions", quiz_id=quiz_id)

        questions = quiz_service.get_quiz_questions(quiz_id)

        return QuizQuestionListResponse(
            data=[QuizQuestionDto(**question.__dict__) for question in questions],
        )

    except Exception as e:
        logger.error_structured("error listing quiz questions", quiz_id=quiz_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list quiz questions",
        )


@router.post(
    path="/{quiz_id}/questions",
    response_model=QuizQuestionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create quiz question",
    description="Create a new quiz question in a quiz",
)
async def create_quiz_question(
    quiz_id: str = Path(..., description="Quiz ID"),
    body: CreateQuizQuestionRequest = Body(...),
    quiz_service: QuizService = Depends(get_quiz_service),
    current_user: User = Depends(get_user),
):
    """Create a new quiz question."""
    try:
        logger.info_structured("creating quiz question", quiz_id=quiz_id, user_id=current_user.id)

        # Get quiz to get project_id
        quiz = quiz_service.get_quiz(quiz_id)
        if not quiz:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quiz not found",
            )

        question = quiz_service.create_quiz_question(
            quiz_id=quiz_id,
            project_id=quiz.project_id,
            question_text=body.question_text,
            option_a=body.option_a,
            option_b=body.option_b,
            option_c=body.option_c,
            option_d=body.option_d,
            correct_option=body.correct_option,
            explanation=body.explanation,
            difficulty_level=body.difficulty_level,
            position=body.position,
        )

        return QuizQuestionResponse(
            question=QuizQuestionDto(**question.__dict__),
            message="Quiz question created successfully",
        )

    except ValueError as e:
        logger.error_structured("error creating quiz question", quiz_id=quiz_id, user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error_structured("error creating quiz question", quiz_id=quiz_id, user_id=current_user.id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create quiz question",
        )


@router.patch(
    path="/{quiz_id}/questions/{question_id}",
    response_model=QuizQuestionResponse,
    status_code=status.HTTP_200_OK,
    summary="Update quiz question",
    description="Update an existing quiz question",
)
async def update_quiz_question(
    quiz_id: str = Path(..., description="Quiz ID"),
    question_id: str = Path(..., description="Question ID"),
    body: UpdateQuizQuestionRequest = Body(...),
    quiz_service: QuizService = Depends(get_quiz_service),
    current_user: User = Depends(get_user),
):
    """Update an existing quiz question."""
    try:
        logger.info_structured("updating quiz question", question_id=question_id, quiz_id=quiz_id, user_id=current_user.id)

        question = quiz_service.update_quiz_question(
            question_id=question_id,
            question_text=body.question_text,
            option_a=body.option_a,
            option_b=body.option_b,
            option_c=body.option_c,
            option_d=body.option_d,
            correct_option=body.correct_option,
            explanation=body.explanation,
            difficulty_level=body.difficulty_level,
        )

        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quiz question not found",
            )

        return QuizQuestionResponse(
            question=QuizQuestionDto(**question.__dict__),
            message="Quiz question updated successfully",
        )

    except Exception as e:
        logger.error_structured("error updating quiz question", question_id=question_id, quiz_id=quiz_id, user_id=current_user.id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update quiz question",
        )


@router.delete(
    path="/{quiz_id}/questions/{question_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete quiz question",
    description="Delete a quiz question",
)
async def delete_quiz_question(
    quiz_id: str = Path(..., description="Quiz ID"),
    question_id: str = Path(..., description="Question ID"),
    quiz_service: QuizService = Depends(get_quiz_service),
    current_user: User = Depends(get_user),
):
    """Delete a quiz question."""
    try:
        logger.info_structured("deleting quiz question", question_id=question_id, quiz_id=quiz_id, user_id=current_user.id)

        success = quiz_service.delete_quiz_question(question_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Quiz question not found",
            )

    except Exception as e:
        logger.error_structured("error deleting quiz question", question_id=question_id, quiz_id=quiz_id, user_id=current_user.id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete quiz question",
        )


@router.patch(
    path="/{quiz_id}/questions/reorder",
    response_model=QuizQuestionListResponse,
    status_code=status.HTTP_200_OK,
    summary="Reorder quiz questions",
    description="Reorder quiz questions in a quiz",
)
async def reorder_quiz_questions(
    quiz_id: str = Path(..., description="Quiz ID"),
    body: ReorderQuizQuestionsRequest = Body(...),
    quiz_service: QuizService = Depends(get_quiz_service),
    current_user: User = Depends(get_user),
):
    """Reorder quiz questions in a quiz."""
    try:
        logger.info_structured("reordering quiz questions", quiz_id=quiz_id, user_id=current_user.id)

        questions = quiz_service.reorder_quiz_questions(
            quiz_id=quiz_id,
            question_ids=body.question_ids,
        )

        return QuizQuestionListResponse(
            data=[QuizQuestionDto(**question.__dict__) for question in questions],
        )

    except ValueError as e:
        logger.error_structured("error reordering quiz questions", quiz_id=quiz_id, user_id=current_user.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error_structured("error reordering quiz questions", quiz_id=quiz_id, user_id=current_user.id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reorder quiz questions",
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
        logger.error_structured("error exporting quiz", quiz_id=quiz_id, user_id=current_user.id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export quiz",
        )
