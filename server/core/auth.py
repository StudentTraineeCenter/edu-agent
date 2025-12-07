from typing import Optional

import jwt as pyjwt
from core.config import app_config
from db.models import User
from db.session import get_db
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

security_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Get the current authenticated user from Supabase JWT token.

    Args:
        credentials: HTTP Bearer token credentials
        db: Database session

    Returns:
        User: The authenticated user

    Raises:
        HTTPException: If authentication fails or user not found
    """
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
            app_config.SUPABASE_JWT_SECRET,
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

        # Look for existing user by ID (which matches auth.users.id)
        user = db.query(User).filter(User.id == supabase_user_id).first()

        if user:
            # Update user information if needed
            if email and user.email != email:
                user.email = email
            if name and user.name != name:
                user.name = name
            db.commit()
            return user
        else:
            # User should be synced from auth.users via database trigger
            # But create it here as fallback if trigger hasn't run yet
            new_user = User(
                id=supabase_user_id,  # Use Supabase user ID as primary key
                email=email,
                name=name or email or f"user_{supabase_user_id[:8]}",
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            return new_user

    except pyjwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except pyjwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
        )


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    Get the current user if authenticated, otherwise return None.
    Useful for endpoints that work with or without authentication.
    """
    if not credentials:
        return None

    try:
        return get_current_user(credentials, db)
    except HTTPException:
        return None


def require_auth(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency that ensures user is authenticated.
    Same as get_current_user but with a more explicit name.
    """
    return current_user
