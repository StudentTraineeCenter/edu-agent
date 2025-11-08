from api.dependencies import get_user, get_usage_service
from core.logger import get_logger
from core.services.usage import UsageService
from db.models import User
from fastapi import APIRouter, Depends, status
from schemas.usage import UsageDto, UsageResponse

logger = get_logger(__name__)

router = APIRouter()


@router.get(
    "",
    response_model=UsageResponse,
    status_code=status.HTTP_200_OK,
    summary="Get usage statistics",
    description="Get current usage statistics for the authenticated user",
)
def get_usage(
    current_user: User = Depends(get_user),
    usage_service: UsageService = Depends(get_usage_service),
) -> UsageResponse:
    """Get current usage statistics for the authenticated user."""
    logger.info("getting usage statistics for user_id=%s", current_user.id)

    usage_dict = usage_service.get_usage(current_user.id)
    usage_dto = UsageDto(**usage_dict)

    return UsageResponse(usage=usage_dto)

