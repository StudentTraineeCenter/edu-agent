"""CRUD service for managing study sessions."""

from contextlib import contextmanager
from datetime import datetime
from typing import Any
from uuid import uuid4

from edu_db.models import StudySession
from edu_db.session import get_session_factory
from edu_core.exceptions import NotFoundError
from edu_core.schemas.study_sessions import StudySessionDto


class StudySessionService:
    """Service for managing study sessions."""

    def __init__(self) -> None:
        """Initialize the study session service."""
        pass

    def create_study_session(
        self,
        user_id: str,
        project_id: str,
        session_length_minutes: int,
        session_data: dict[str, Any] | None = None,
        focus_topics: list[str] | None = None,
    ) -> StudySessionDto:
        """Create a new study session.

        Args:
            user_id: The user ID
            project_id: The project ID
            session_length_minutes: Requested session length in minutes
            session_data: Optional session data (flashcards, learning_objectives, etc.)
            focus_topics: Optional focus topics

        Returns:
            Created StudySessionDto
        """
        with self._get_db_session() as db:
            try:
                session_data = session_data or {
                    "flashcards": [],
                    "learning_objectives": [],
                }
                estimated_time = session_length_minutes

                study_session = StudySession(
                    id=str(uuid4()),
                    user_id=user_id,
                    project_id=project_id,
                    session_data=session_data,
                    estimated_time_minutes=estimated_time,
                    session_length_minutes=session_length_minutes,
                    focus_topics=focus_topics,
                    generated_at=datetime.now(),
                )
                db.add(study_session)
                db.commit()
                db.refresh(study_session)

                return self._model_to_dto(study_session)
            except Exception:
                db.rollback()
                raise

    def get_study_session(self, session_id: str, user_id: str) -> StudySessionDto:
        """Get a study session by ID.

        Args:
            session_id: The study session ID
            user_id: The user ID

        Returns:
            StudySessionDto

        Raises:
            NotFoundError: If study session not found
        """
        with self._get_db_session() as db:
            try:
                session = (
                    db.query(StudySession)
                    .filter(
                        StudySession.id == session_id,
                        StudySession.user_id == user_id,
                    )
                    .first()
                )
                if not session:
                    raise NotFoundError(f"Study session {session_id} not found")

                return self._model_to_dto(session)
            except NotFoundError:
                raise
            except Exception:
                raise

    def list_study_sessions(
        self, project_id: str, user_id: str, limit: int = 50
    ) -> list[StudySessionDto]:
        """List all study sessions for a project.

        Args:
            project_id: The project ID
            user_id: The user ID
            limit: Maximum number of sessions to return

        Returns:
            List of StudySessionDto instances
        """
        with self._get_db_session() as db:
            try:
                sessions = (
                    db.query(StudySession)
                    .filter(
                        StudySession.project_id == project_id,
                        StudySession.user_id == user_id,
                    )
                    .order_by(StudySession.generated_at.desc())
                    .limit(limit)
                    .all()
                )
                return [self._model_to_dto(s) for s in sessions]
            except Exception:
                raise

    def _model_to_dto(self, session: StudySession) -> StudySessionDto:
        """Convert StudySession model to StudySessionDto."""
        return StudySessionDto(
            id=session.id,
            user_id=session.user_id,
            project_id=session.project_id,
            session_data=session.session_data,
            estimated_time_minutes=session.estimated_time_minutes,
            session_length_minutes=session.session_length_minutes,
            focus_topics=session.focus_topics,
            generated_at=session.generated_at,
            started_at=session.started_at,
            completed_at=session.completed_at,
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
