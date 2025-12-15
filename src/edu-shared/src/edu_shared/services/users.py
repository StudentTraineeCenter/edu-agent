"""CRUD service for managing users."""

from contextlib import contextmanager

from edu_core.db.models import User
from edu_core.db.session import get_session_factory
from edu_core.exceptions import NotFoundError
from edu_core.schemas.users import UserDto


class UserService:
    """Service for managing users."""

    def __init__(self) -> None:
        """Initialize the user service."""
        pass

    def get_user(self, user_id: str) -> UserDto:
        """Get a user by ID.

        Args:
            user_id: The user ID

        Returns:
            UserDto

        Raises:
            NotFoundError: If user not found
        """
        with self._get_db_session() as db:
            try:
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    raise NotFoundError(f"User {user_id} not found")

                return self._model_to_dto(user)
            except NotFoundError:
                raise
            except Exception:
                raise

    def list_users(self) -> list[UserDto]:
        """List all users.

        Returns:
            List of UserDto instances
        """
        with self._get_db_session() as db:
            try:
                users = db.query(User).order_by(User.created_at.desc()).all()
                return [self._model_to_dto(user) for user in users]
            except Exception:
                raise

    def delete_user(self, user_id: str) -> None:
        """Delete a user.

        Args:
            user_id: The user ID

        Raises:
            NotFoundError: If user not found
        """
        with self._get_db_session() as db:
            try:
                user = db.query(User).filter(User.id == user_id).first()
                if not user:
                    raise NotFoundError(f"User {user_id} not found")

                db.delete(user)
                db.commit()
            except NotFoundError:
                raise
            except Exception:
                db.rollback()
                raise

    def get_or_create_user_from_token(
        self,
        user_id: str,
        email: str | None = None,
        name: str | None = None,
    ) -> UserDto:
        """Get or create a user from JWT token data.
        
        Args:
            user_id: The user ID from JWT token (sub claim)
            email: Optional email from token
            name: Optional name from token
            
        Returns:
            UserDto: The user DTO
        """
        with self._get_db_session() as db:
            try:
                # Try to get existing user
                user = db.query(User).filter(User.id == user_id).first()

                if user:
                    # Update user information if needed
                    updated = False
                    if email and user.email != email:
                        user.email = email
                        updated = True
                    if name and user.name != name:
                        user.name = name
                        updated = True

                    if updated:
                        db.commit()
                        db.refresh(user)

                    return self._model_to_dto(user)
                else:
                    # User should be synced from auth.users via database trigger
                    # But create it here as fallback if trigger hasn't run yet
                    new_user = User(
                        id=user_id,
                        email=email,
                        name=name or email.split("@")[0] or f"user_{user_id[:8]}",
                    )
                    db.add(new_user)
                    db.commit()
                    db.refresh(new_user)
                    return self._model_to_dto(new_user)
            except Exception:
                db.rollback()
                raise

    def _model_to_dto(self, user: User) -> UserDto:
        """Convert User model to UserDto."""
        return UserDto(
            id=user.id,
            name=user.name,
            email=user.email,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )

    @contextmanager
    def _get_db_session(self):
        """Context manager for database sessions."""
        SessionLocal = get_session_factory()
        db = SessionLocal()
        try:
            yield db
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

