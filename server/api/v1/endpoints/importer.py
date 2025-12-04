from api.dependencies import get_importer_service, get_user
from core.logger import get_logger
from core.services.importer import ImporterService
from db.models import User
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel

router = APIRouter()

logger = get_logger(__name__)


class ImportResponse(BaseModel):
    id: str


@router.post(
    "/projects/{project_id}/flashcard-groups/import",
    response_model=ImportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Import flashcard group from CSV",
    description="Import flashcards from CSV file"
)
async def import_flashcard_group(
    project_id: str,
    file: UploadFile = File(...),
    group_name: str = Form(...),
    group_description: str | None = Form(None),
    importer_service: ImporterService = Depends(get_importer_service),
    current_user: User = Depends(get_user),
):
    """Import flashcard group from CSV."""
    try:
        # Read CSV content
        csv_content = await file.read()
        csv_content_str = csv_content.decode("utf-8")

        group_id = importer_service.import_flashcards_from_csv(
            project_id=project_id,
            csv_content=csv_content_str,
            group_name=group_name,
            group_description=group_description
        )

        return ImportResponse(
            id=group_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"error importing flashcard group: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to import flashcard group"
        )


@router.post(
    "/projects/{project_id}/quizzes/import",
    response_model=ImportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Import quiz from CSV",
    description="Import quiz from CSV file"
)
async def import_quiz(
    project_id: str,
    file: UploadFile = File(...),
    quiz_name: str = Form(...),
    quiz_description: str | None = Form(None),
    importer_service: ImporterService = Depends(get_importer_service),
    current_user: User = Depends(get_user),
):
    """Import quiz from CSV."""
    try:
        # Read CSV content
        csv_content = await file.read()
        csv_content_str = csv_content.decode("utf-8")

        quiz_id = importer_service.import_quiz_from_csv(
            project_id=project_id,
            csv_content=csv_content_str,
            quiz_name=quiz_name,
            quiz_description=quiz_description
        )

        return ImportResponse(
            id=quiz_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"error importing quiz: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to import quiz"
        )

