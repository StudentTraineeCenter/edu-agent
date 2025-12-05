"""Service for managing projects."""

from contextlib import contextmanager
from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from core.exceptions import NotFoundError
from core.logger import get_logger
from db.models import Project
from db.session import SessionLocal

logger = get_logger(__name__)


class ProjectService:
    """Service for managing projects."""

    def __init__(self) -> None:
        """Initialize the project service."""
        pass

    def create_project(
        self,
        owner_id: str,
        name: str,
        description: Optional[str] = None,
        language_code: Optional[str] = "en",
    ) -> Project:
        """Create a new project.

        Args:
            owner_id: The project owner's user ID
            name: The project name
            description: Optional project description
            language_code: Language code for the project (default: "en")

        Returns:
            Created Project model instance

        Raises:
            ValueError: If project creation fails
        """
        with self._get_db_session() as db:
            try:
                project = Project(
                    id=str(uuid4()),
                    owner_id=owner_id,
                    name=name,
                    description=description,
                    language_code=language_code or "en",
                    created_at=datetime.now(),
                )
                db.add(project)
                db.commit()
                db.refresh(project)

                logger.info(f"created project project_id={project.id}")
                return project
            except Exception as e:
                logger.error(f"error creating project for owner_id={owner_id}: {e}")
                raise

    def get_project(self, project_id: str, owner_id: str) -> Project:
        """Get a project by ID.

        Args:
            project_id: The project ID
            owner_id: The project owner's user ID

        Returns:
            Project model instance

        Raises:
            NotFoundError: If project not found
        """
        with self._get_db_session() as db:
            try:
                project = (
                    db.query(Project)
                    .filter(Project.id == project_id, Project.owner_id == owner_id)
                    .first()
                )
                if not project:
                    raise NotFoundError(f"Project {project_id} not found")

                logger.info(f"retrieved project project_id={project_id}")
                return project
            except NotFoundError:
                raise
            except Exception as e:
                logger.error(f"error getting project project_id={project_id}: {e}")
                raise

    def list_projects(self, owner_id: str) -> List[Project]:
        """List all projects for a user.

        Args:
            owner_id: The project owner's user ID

        Returns:
            List of Project model instances
        """
        with self._get_db_session() as db:
            try:
                projects = (
                    db.query(Project)
                    .filter(Project.owner_id == owner_id)
                    .order_by(Project.created_at.desc())
                    .all()
                )
                logger.info(f"listed {len(projects)} projects for owner_id={owner_id}")
                return projects
            except Exception as e:
                logger.error(f"error listing projects for owner_id={owner_id}: {e}")
                raise

    def check_exists(self, owner_id: str, name: str) -> bool:
        """Check if a project exists.

        Args:
            owner_id: The project owner's user ID
            name: The project name to check

        Returns:
            True if project exists, False otherwise
        """
        with self._get_db_session() as db:
            try:
                project = (
                    db.query(Project)
                    .filter(Project.owner_id == owner_id, Project.name == name)
                    .first()
                )
                exists = project is not None
                logger.info(
                    f"checked project existence owner_id={owner_id}, name={name}, exists={exists}"
                )
                return exists
            except Exception as e:
                logger.error(
                    f"error checking if project exists for owner_id={owner_id}, name={name}: {e}"
                )
                raise

    def update_project(
        self,
        project_id: str,
        owner_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        language_code: Optional[str] = None,
    ) -> Project:
        """Update a project.

        Args:
            project_id: The project ID
            owner_id: The project owner's user ID
            name: Optional new project name
            description: Optional new project description
            language_code: Optional new language code

        Returns:
            Updated Project model instance

        Raises:
            NotFoundError: If project not found
        """
        with self._get_db_session() as db:
            try:
                project = (
                    db.query(Project)
                    .filter(Project.id == project_id, Project.owner_id == owner_id)
                    .first()
                )
                if not project:
                    raise NotFoundError(f"Project {project_id} not found")

                if name is not None:
                    project.name = name
                if description is not None:
                    project.description = description
                if language_code is not None:
                    project.language_code = language_code

                db.commit()
                db.refresh(project)

                logger.info(f"updated project project_id={project_id}")
                return project
            except NotFoundError:
                raise
            except Exception as e:
                logger.error(f"error updating project project_id={project_id}: {e}")
                raise

    def delete_project(self, project_id: str, owner_id: str) -> None:
        """Delete a project.

        Args:
            project_id: The project ID
            owner_id: The project owner's user ID

        Raises:
            NotFoundError: If project not found
        """
        with self._get_db_session() as db:
            try:
                project = (
                    db.query(Project)
                    .filter(Project.id == project_id, Project.owner_id == owner_id)
                    .first()
                )
                if not project:
                    raise NotFoundError(f"Project {project_id} not found")

                db.delete(project)
                db.commit()

                logger.info(f"deleted project project_id={project_id}")
            except NotFoundError:
                raise
            except Exception as e:
                logger.error(f"error deleting project project_id={project_id}: {e}")
                raise

    @contextmanager
    def _get_db_session(self):
        """Context manager for database sessions."""
        db = SessionLocal()
        try:
            yield db
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
