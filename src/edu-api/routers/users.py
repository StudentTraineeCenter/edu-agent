"""Router for user operations."""

from fastapi import APIRouter, HTTPException, Header

from edu_shared.services import UserService, NotFoundError
from edu_shared.schemas.users import UserDto

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("/{user_id}", response_model=UserDto)
async def get_user(
    user_id: str,
):
    """Get a user by ID."""
    service = UserService()
    try:
        return service.get_user(user_id=user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=list[UserDto])
async def list_users():
    """List all users."""
    service = UserService()
    try:
        return service.list_users()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: str,
):
    """Delete a user."""
    service = UserService()
    try:
        service.delete_user(user_id=user_id)
        return None
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

