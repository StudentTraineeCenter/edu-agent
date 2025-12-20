from typing import Annotated

from dependencies import get_study_plan_service
from fastapi import APIRouter, Depends, status

from edu_core.schemas.study_plans import StudyPlanDto
from edu_core.services.study_plans import StudyPlanService
from .auth import get_current_user

study_plans_router = APIRouter(
    prefix="/api/v1/projects/{project_id}/study-plans", tags=["Study Plans"]
)


@study_plans_router.get("/latest", response_model=StudyPlanDto | None)
def get_latest_study_plan(
    project_id: str,
    user=Depends(get_current_user),
    service=Depends(get_study_plan_service)
):
    """Get the latest study plan for the user in the project."""
    return service.get_latest_study_plan(user.id, project_id)


@study_plans_router.get("", response_model=list[StudyPlanDto])
def list_study_plans(
    project_id: str,
    user=Depends(get_current_user),
    service=Depends(get_study_plan_service)
):
    """List all study plans for the user in the project."""
    return service.list_study_plans(user.id, project_id)


@study_plans_router.post(
    "/generate", response_model=StudyPlanDto, status_code=status.HTTP_201_CREATED
)
async def generate_study_plan(
    project_id: str,
    user=Depends(get_current_user),
    service=Depends(get_study_plan_service),
):
    """Generate a new study plan for the user based on performance."""
    return await service.generate_study_plan(user.id, project_id)
