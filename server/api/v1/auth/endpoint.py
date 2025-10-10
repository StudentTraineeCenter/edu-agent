from fastapi import APIRouter, Depends, HTTPException
from api.v1.deps import get_user
from db.model import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_user)):
    """Get authenticated user information (requires auth)"""

    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "azure_oid": current_user.azure_oid,
        "created_at": current_user.created_at.isoformat(),
    }
