
import jwt as pyjwt
from config import get_settings
from edu_shared.schemas.users import UserDto
from edu_shared.services import UserService
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

security_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
) -> UserDto:
    """
    Get the current authenticated user from Supabase JWT token.

    Args:
        credentials: HTTP Bearer token credentials

    Returns:
        UserDto: The authenticated user

    Raises:
        HTTPException: If authentication fails or user not found
    """
    settings = get_settings()
    supabase_jwt_secret = settings.supabase_jwt_secret

    if not supabase_jwt_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supabase JWT secret not configured",
        )

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        # Verify and decode Supabase JWT token
        # Supabase uses HS256 algorithm with the JWT secret
        payload = pyjwt.decode(
            token,
            supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
        )

        # Extract Supabase user ID (sub claim) - this is the UUID from auth.users
        supabase_user_id = payload.get("sub")
        if not supabase_user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID",
            )

        # Extract user information from token
        email = payload.get("email")
        # Supabase tokens include user_metadata and app_metadata
        user_metadata = payload.get("user_metadata", {})
        app_metadata = payload.get("app_metadata", {})

        # Get name from user_metadata or email
        name = user_metadata.get("name") or user_metadata.get("full_name")
        if not name and email:
            # Fallback to email username part
            name = email.split("@")[0]

        # Use UserService to get or create user (doesn't expose DB directly)
        user_service = UserService()
        user_dto = user_service.get_or_create_user_from_token(
            user_id=supabase_user_id,
            email=email,
            name=name,
        )

        return user_dto

    except pyjwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except pyjwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e!s}",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {e!s}",
        )


def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
) -> UserDto | None:
    """
    Get the current user if authenticated, otherwise return None.
    Useful for endpoints that work with or without authentication.
    """
    if not credentials:
        return None

    settings = get_settings()
    jwt_secret = settings.supabase_jwt_secret
    if not jwt_secret:
        return None

    try:
        return get_current_user(credentials)
    except HTTPException:
        return None
