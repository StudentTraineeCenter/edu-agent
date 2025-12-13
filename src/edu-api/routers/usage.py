"""Router for usage statistics."""

from fastapi import APIRouter, Depends, status

from auth import get_current_user
from dependencies import get_usage_service
from edu_shared.schemas.usage import UsageDto
from edu_shared.services import UsageService
from edu_shared.schemas.users import UserDto

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

