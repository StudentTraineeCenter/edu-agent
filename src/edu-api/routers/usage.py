"""Router for usage statistics."""

from auth import get_current_user
from dependencies import get_usage_service
from edu_core.schemas.usage import UsageDto
from edu_core.schemas.users import UserDto
from edu_core.services import UsageService
from fastapi import APIRouter, Depends, status

router = APIRouter(prefix="/api/v1/usage", tags=["usage"])


@router.get(
    "",
    response_model=UsageDto,
    status_code=status.HTTP_200_OK,
    summary="Get usage statistics",
    description="Get current usage statistics for the authenticated user",
)
async def get_usage(
    current_user: UserDto = Depends(get_current_user),
    usage_service: UsageService = Depends(get_usage_service),
) -> UsageDto:
    """Get current usage statistics for the authenticated user."""
    usage = usage_service.get_usage(current_user.id)

    return usage
