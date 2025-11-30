from api.dependencies import get_study_plan_service, get_user
from core.logger import get_logger
from core.services.study_plans import StudyPlanService
from db.models import User
from fastapi import APIRouter, Depends, HTTPException, status
from schemas.study_plans import StudyPlanDto

logger = get_logger(__name__)

router = APIRouter()


@router.get(
    "/projects/{project_id}/study-plans",
    response_model=StudyPlanDto,
    status_code=status.HTTP_200_OK,
    summary="Get study plan",
    description="Get the latest study plan for a project (1 plan per project)",
)
async def get_study_plan(
    project_id: str,
    study_plan_service: StudyPlanService = Depends(get_study_plan_service),
    current_user: User = Depends(get_user),
):
    """Get the latest study plan for a project."""
    try:
        logger.info(
            f"getting study plan for project_id={project_id}, user_id={current_user.id}"
        )

        plan = study_plan_service.get_latest_plan(
            user_id=current_user.id, project_id=project_id
        )

        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No study plan found. Generate one first.",
            )

        return StudyPlanDto.model_validate(plan)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"error getting study plan: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get study plan",
        )


@router.post(
    "/projects/{project_id}/study-plans",
    response_model=StudyPlanDto,
    status_code=status.HTTP_201_CREATED,
    summary="Generate study plan",
    description="Generate or regenerate personalized study plan based on performance",
)
async def generate_study_plan(
    project_id: str,
    study_plan_service: StudyPlanService = Depends(get_study_plan_service),
    current_user: User = Depends(get_user),
):
    """Generate a new personalized study plan (replaces existing one if it exists)."""
    try:
        logger.info(
            f"generating study plan for project_id={project_id}, user_id={current_user.id}"
        )

        plan = await study_plan_service.generate_study_plan(
            user_id=current_user.id, project_id=project_id
        )

        return StudyPlanDto.model_validate(plan)
    except ValueError as e:
        logger.error(f"validation error generating study plan: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"error generating study plan: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate study plan",
        )

