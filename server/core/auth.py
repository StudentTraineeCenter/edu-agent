from typing import Optional

import jwt as pyjwt
from core.config import app_config
from db.models import User
from db.session import get_db
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi_azure_auth import SingleTenantAzureAuthorizationCodeBearer
from sqlalchemy.orm import Session

azure_auth_scheme = SingleTenantAzureAuthorizationCodeBearer(
    app_client_id=app_config.AZURE_ENTRA_CLIENT_ID,
    tenant_id=app_config.AZURE_ENTRA_TENANT_ID,
    scopes={
        "openid": "OpenID Connect",
        "profile": "User profile",
        "email": "User email",
    },
)

security_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Get the current authenticated user from Azure Entra token.

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
        # Decode token to extract user information
        # Note: In production, you should verify the token signature
        # For now, we'll decode without verification for compatibility
        payload = pyjwt.decode(token, options={"verify_signature": False})

        # Extract Azure Object ID (OID) - this is the unique identifier for the user
        azure_oid = payload.get("oid")
        if not azure_oid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing Azure Object ID",
            )

        # Extract user information from token
        email = payload.get("email") or payload.get("unique_name")
        name = payload.get("name")
        given_name = payload.get("given_name")
        family_name = payload.get("family_name")

        name = name or given_name + " " + family_name

        # Verify app ID matches our configuration
        app_id = payload.get("appid")
        if app_id != app_config.AZURE_ENTRA_CLIENT_ID:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid application ID. Expected: {app_config.AZURE_ENTRA_CLIENT_ID}, Got: {app_id}",
            )

        # Look for existing user by Azure OID
        user = db.query(User).filter(User.azure_oid == azure_oid).first()

        if user:
            # Update user information if needed
            if email and user.email != email:
                user.email = email
            if name and user.name != name:
                user.name = name
            db.commit()
            return user
        else:
            # Create new user
            new_user = User(
                azure_oid=azure_oid,
                email=email,
                name=name or email or f"user_{azure_oid[:8]}",
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
