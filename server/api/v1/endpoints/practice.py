from api.dependencies import get_practice_service, get_user
from core.logger import get_logger
from core.services.practice import PracticeService
from db.models import User
from fastapi import APIRouter, Depends, HTTPException, Query, status
from schemas.practice import (
    CreatePracticeRecordBatchRequest,
    CreatePracticeRecordRequest,
    PracticeRecordDto,
    PracticeRecordListResponse,
    PracticeRecordResponse,
)

logger = get_logger(__name__)

router = APIRouter()


@router.post(
    path="",
    response_model=PracticeRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a practice record",
    description="Create a new practice record for a flashcard or quiz question",
)
async def create_practice_record(
    project_id: str,
    request: CreatePracticeRecordRequest,
    practice_service: PracticeService = Depends(get_practice_service),
    current_user: User = Depends(get_user),
):
    """Create a new practice record."""
    try:
        logger.info(
            "creating practice record for project_id=%s, user_id=%s, item_type=%s, item_id=%s",
            project_id,
            current_user.id,
            request.item_type,
            request.item_id,
        )

        practice_record = practice_service.create_practice_record(
            user_id=current_user.id,
            project_id=project_id,
            study_resource_type=request.item_type,
            study_resource_id=request.item_id,
            topic=request.topic,
            user_answer=request.user_answer,
            correct_answer=request.correct_answer,
            was_correct=request.was_correct,
            quality_rating=request.quality_rating,
        )

        return PracticeRecordResponse(
            practice_record=PracticeRecordDto(
                id=practice_record.id,
                user_id=practice_record.user_id,
                project_id=practice_record.project_id,
                item_type=practice_record.item_type,
                item_id=practice_record.item_id,
                topic=practice_record.topic,
                user_answer=practice_record.user_answer,
                correct_answer=practice_record.correct_answer,
                was_correct=practice_record.was_correct,
                created_at=practice_record.created_at,
            ),
            message="Practice record created successfully",
        )

    except ValueError as e:
        logger.error("validation error creating practice record: %s", e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error("error creating practice record: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create practice record",
        )


@router.post(
    path="/batch",
    response_model=PracticeRecordListResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create multiple practice records",
    description="Create multiple practice records in a single batch operation",
)
async def create_practice_records_batch(
    project_id: str,
    request: CreatePracticeRecordBatchRequest,
    practice_service: PracticeService = Depends(get_practice_service),
    current_user: User = Depends(get_user),
):
    """Create multiple practice records in a batch."""
    try:
        logger.info(
            "creating batch of %d practice records for project_id=%s, user_id=%s",
            len(request.practice_records),
            project_id,
            current_user.id,
        )

        practice_records_data = [
            {
                "item_type": record.item_type,
                "item_id": record.item_id,
                "topic": record.topic,
                "user_answer": record.user_answer,
                "correct_answer": record.correct_answer,
                "was_correct": record.was_correct,
            }
            for record in request.practice_records
        ]

        created_records = practice_service.create_practice_records_batch(
            user_id=current_user.id,
            project_id=project_id,
            practice_records_data=practice_records_data,
        )

        return PracticeRecordListResponse(
            data=[
                PracticeRecordDto(
                    id=record.id,
                    user_id=record.user_id,
                    project_id=record.project_id,
                    item_type=record.item_type,
                    item_id=record.item_id,
                    topic=record.topic,
                    user_answer=record.user_answer,
                    correct_answer=record.correct_answer,
                    was_correct=record.was_correct,
                    created_at=record.created_at,
                )
                for record in created_records
            ],
        )

    except ValueError as e:
        logger.error("validation error creating practice records batch: %s", e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error("error creating practice records batch: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create practice records batch",
        )


@router.get(
    path="",
    response_model=PracticeRecordListResponse,
    status_code=status.HTTP_200_OK,
    summary="List practice records",
    description="List practice records for the current user, optionally filtered by project",
)
async def list_practice_records(
    project_id: str | None = Query(None, description="Optional project ID filter"),
    practice_service: PracticeService = Depends(get_practice_service),
    current_user: User = Depends(get_user),
):
    """List practice records for the current user."""
    try:
        logger.info(
            "listing practice records for user_id=%s, project_id=%s",
            current_user.id,
            project_id,
        )

        records = practice_service.get_user_practice_records(
            user_id=current_user.id, project_id=project_id
        )

        return PracticeRecordListResponse(
            data=[
                PracticeRecordDto(
                    id=record.id,
                    user_id=record.user_id,
                    project_id=record.project_id,
                    item_type=record.item_type,
                    item_id=record.item_id,
                    topic=record.topic,
                    user_answer=record.user_answer,
                    correct_answer=record.correct_answer,
                    was_correct=record.was_correct,
                    created_at=record.created_at,
                )
                for record in records
            ],
        )

    except Exception as e:
        logger.error("error listing practice records: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list practice records",
        )
