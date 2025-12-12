"""Router for authentication operations."""

from fastapi import APIRouter, Depends

from auth import get_current_user
from edu_shared.schemas.users import UserDto

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.get("/me", response_model=UserDto)
async def get_current_user_info(
    current_user: UserDto = Depends(get_current_user),
) -> UserDto:
    """Get authenticated user information (requires auth)"""
    return current_user

