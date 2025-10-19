from api.dependencies import get_user
from db.models import User
from fastapi import APIRouter, Depends, HTTPException
from schemas.auth import UserDto

router = APIRouter()


@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_user)) -> UserDto:
    """Get authenticated user information (requires auth)"""

    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    return UserDto(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        azure_oid=current_user.azure_oid,
        created_at=current_user.created_at.isoformat(),
    )
