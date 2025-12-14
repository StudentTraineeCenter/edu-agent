"""Router for practice record operations."""

from auth import get_current_user
from dependencies import get_practice_service
from edu_shared.schemas.practice import PracticeRecordDto
from edu_shared.schemas.users import UserDto
from edu_shared.services import PracticeService
from fastapi import APIRouter, Depends, HTTPException

from routers.schemas import PracticeRecordBatchCreate, PracticeRecordCreate

router = APIRouter(prefix="/api/v1/projects/{project_id}/practice-records", tags=["practice-records"])


@router.get("", response_model=list[PracticeRecordDto])
async def list_practice_records(
    project_id: str,
    current_user: UserDto = Depends(get_current_user),
    service: PracticeService = Depends(get_practice_service),
):
    """List practice records for a project."""
    try:
        return service.list_practice_records(
            user_id=current_user.id,
            project_id=project_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=PracticeRecordDto, status_code=201)
async def create_practice_record(
    project_id: str,
    record: PracticeRecordCreate,
    current_user: UserDto = Depends(get_current_user),
    service: PracticeService = Depends(get_practice_service),
):
    """Create a single practice record."""
    try:
        return service.create_practice_record(
            user_id=current_user.id,
            project_id=project_id,
            item_type=record.item_type,
            item_id=record.item_id,
            topic=record.topic,
            user_answer=record.user_answer,
            correct_answer=record.correct_answer,
            was_correct=record.was_correct,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch", response_model=list[PracticeRecordDto], status_code=201)
async def create_practice_records_batch(
    project_id: str,
    batch: PracticeRecordBatchCreate,
    current_user: UserDto = Depends(get_current_user),
    service: PracticeService = Depends(get_practice_service),
):
    """Create multiple practice records."""
    try:
        records_data = [
            {
                "item_type": r.item_type,
                "item_id": r.item_id,
                "topic": r.topic,
                "user_answer": r.user_answer,
                "correct_answer": r.correct_answer,
                "was_correct": r.was_correct,
            }
            for r in batch.practice_records
        ]
        return service.create_practice_records_batch(
            user_id=current_user.id,
            project_id=project_id,
            practice_records_data=records_data,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

