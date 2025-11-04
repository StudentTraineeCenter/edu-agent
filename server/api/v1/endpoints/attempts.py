from api.dependencies import get_attempt_service, get_user
from core.logger import get_logger
from core.services.attempts import AttemptService
from db.models import User
from fastapi import APIRouter, Depends, HTTPException, Query, status
from schemas.attempts import (
    AttemptDto,
    AttemptListResponse,
    AttemptResponse,
    CreateAttemptBatchRequest,
    CreateAttemptRequest,
)

logger = get_logger(__name__)

router = APIRouter()


@router.post(
    path="",
    response_model=AttemptResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an attempt record",
    description="Create a new study attempt record for a flashcard or quiz question",
)
async def create_attempt(
    project_id: str,
    request: CreateAttemptRequest,
    attempt_service: AttemptService = Depends(get_attempt_service),
    current_user: User = Depends(get_user),
):
    """Create a new study attempt record."""
    try:
        logger.info(
            "creating attempt for project_id=%s, user_id=%s, item_type=%s, item_id=%s",
            project_id,
            current_user.id,
            request.item_type,
            request.item_id,
        )

        attempt = attempt_service.create_attempt(
            user_id=current_user.id,
            project_id=project_id,
            item_type=request.item_type,
            item_id=request.item_id,
            topic=request.topic,
            user_answer=request.user_answer,
            correct_answer=request.correct_answer,
            was_correct=request.was_correct,
        )

        return AttemptResponse(
            attempt=AttemptDto(
                id=attempt.id,
                user_id=attempt.user_id,
                project_id=attempt.project_id,
                item_type=attempt.item_type,
                item_id=attempt.item_id,
                topic=attempt.topic,
                user_answer=attempt.user_answer,
                correct_answer=attempt.correct_answer,
                was_correct=attempt.was_correct,
                created_at=attempt.created_at,
            ),
            message="Attempt created successfully",
        )

    except ValueError as e:
        logger.error("validation error creating attempt: %s", e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error("error creating attempt: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create attempt",
        )


@router.post(
    path="/batch",
    response_model=AttemptListResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create multiple attempt records",
    description="Create multiple study attempt records in a single batch operation",
)
async def create_attempts_batch(
    project_id: str,
    request: CreateAttemptBatchRequest,
    attempt_service: AttemptService = Depends(get_attempt_service),
    current_user: User = Depends(get_user),
):
    """Create multiple study attempt records in a batch."""
    try:
        logger.info(
            "creating batch of %d attempts for project_id=%s, user_id=%s",
            len(request.attempts),
            project_id,
            current_user.id,
        )

        attempts_data = [
            {
                "item_type": attempt.item_type,
                "item_id": attempt.item_id,
                "topic": attempt.topic,
                "user_answer": attempt.user_answer,
                "correct_answer": attempt.correct_answer,
                "was_correct": attempt.was_correct,
            }
            for attempt in request.attempts
        ]

        created_attempts = attempt_service.create_attempts_batch(
            user_id=current_user.id,
            project_id=project_id,
            attempts_data=attempts_data,
        )

        return AttemptListResponse(
            attempts=[
                AttemptDto(
                    id=attempt.id,
                    user_id=attempt.user_id,
                    project_id=attempt.project_id,
                    item_type=attempt.item_type,
                    item_id=attempt.item_id,
                    topic=attempt.topic,
                    user_answer=attempt.user_answer,
                    correct_answer=attempt.correct_answer,
                    was_correct=attempt.was_correct,
                    created_at=attempt.created_at,
                )
                for attempt in created_attempts
            ],
            total=len(created_attempts),
        )

    except ValueError as e:
        logger.error("validation error creating attempts batch: %s", e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error("error creating attempts batch: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create attempts batch",
        )


@router.get(
    path="",
    response_model=AttemptListResponse,
    status_code=status.HTTP_200_OK,
    summary="List attempt records",
    description="List study attempt records for the current user, optionally filtered by project",
)
async def list_attempts(
    project_id: str | None = Query(None, description="Optional project ID filter"),
    attempt_service: AttemptService = Depends(get_attempt_service),
    current_user: User = Depends(get_user),
):
    """List study attempt records for the current user."""
    try:
        logger.info(
            "listing attempts for user_id=%s, project_id=%s",
            current_user.id,
            project_id,
        )

        attempts = attempt_service.get_user_attempts(
            user_id=current_user.id, project_id=project_id
        )

        return AttemptListResponse(
            attempts=[
                AttemptDto(
                    id=attempt.id,
                    user_id=attempt.user_id,
                    project_id=attempt.project_id,
                    item_type=attempt.item_type,
                    item_id=attempt.item_id,
                    topic=attempt.topic,
                    user_answer=attempt.user_answer,
                    correct_answer=attempt.correct_answer,
                    was_correct=attempt.was_correct,
                    created_at=attempt.created_at,
                )
                for attempt in attempts
            ],
            total=len(attempts),
        )

    except Exception as e:
        logger.error("error listing attempts: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list attempts",
        )

