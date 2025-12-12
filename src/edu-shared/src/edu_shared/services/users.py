"""CRUD service for managing users."""

from contextlib import contextmanager
from typing import List

from edu_shared.db.models import User
from edu_shared.db.session import get_session_factory
from edu_shared.schemas.users import UserDto
from edu_shared.exceptions import NotFoundError


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
            except Exception as e:
                raise

    def list_users(self) -> List[UserDto]:
        """List all users.

        Returns:
            List of UserDto instances
        """
        with self._get_db_session() as db:
            try:
                users = db.query(User).order_by(User.created_at.desc()).all()
                return [self._model_to_dto(user) for user in users]
            except Exception as e:
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
            except Exception as e:
                db.rollback()
                raise

    def _model_to_dto(self, user: User) -> UserDto:
        """Convert User model to UserDto."""
        return UserDto(
            id=user.id,
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

