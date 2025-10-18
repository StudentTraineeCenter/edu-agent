from contextlib import contextmanager
from datetime import datetime
from typing import Optional
from uuid import uuid4

from core.logger import get_logger

from db.model import Project
from db.session import SessionLocal

logger = get_logger(__name__)


class ProjectService:
    def __init__(self):
        pass

    def create_project(
        self,
        owner_id: str,
        name: str,
        description: Optional[str] = None,
        language_code: Optional[str] = "en",
    ) -> Project:
        """Create a new project"""

        with self._get_db_session() as db:
            try:
                project: Project = Project(
                    id=str(uuid4()),
                    owner_id=owner_id,
                    name=name,
                    description=description,
                    language_code=language_code or "en",
                    created_at=datetime.now(),
                    archived_at=None,
                )
                db.add(project)
                db.commit()
                db.refresh(project)

                logger.info(f"Project created: {project.id}")
                return project
            except Exception as e:
                logger.error(f"Error creating project: {e}")
                raise

    def get_project(self, project_id: str, owner_id: str) -> Optional[Project]:
        """Get a project by id"""
        with self._get_db_session() as db:
            try:
                project: Optional[Project] = (
                    db.query(Project)
                    .filter(Project.id == project_id, Project.owner_id == owner_id)
                    .first()
                )
                if not project:
                    raise ValueError(f"Project with id {project_id} not found")

                logger.info(f"Found project: {project_id}")

                return project
            except Exception as e:
                logger.error(f"Error getting project: {e}")
                raise

    def list_projects(self, owner_id: str) -> list[Project]:
        """List all projects for a user"""
        with self._get_db_session() as db:
            try:
                projects: list[Project] = (
                    db.query(Project).filter(Project.owner_id == owner_id).all()
                )
                return projects
            except Exception as e:
                logger.error(f"Error listing projects: {e}")
                raise e

    def check_exists(self, owner_id: str, name: str) -> bool:
        """Check if a project exists"""
        with self._get_db_session() as db:
            try:
                project: Optional[Project] = (
                    db.query(Project)
                    .filter(Project.owner_id == owner_id, Project.name == name)
                    .first()
                )
                return project is not None
            except Exception as e:
                logger.error(f"Error checking if project exists: {e}")
                raise

    def update_project(
        self,
        project_id: str,
        owner_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        language_code: Optional[str] = None,
    ) -> Project:
        """Update a project"""
        with self._get_db_session() as db:
            try:
                project: Optional[Project] = (
                    db.query(Project)
                    .filter(Project.id == project_id, Project.owner_id == owner_id)
                    .first()
                )
                if not project:
                    raise ValueError(f"Project with id {project_id} not found")

                if name is not None:
                    project.name = name
                if description is not None:
                    project.description = description
                if language_code is not None:
                    project.language_code = language_code

                db.commit()
                db.refresh(project)

                return project
            except Exception as e:
                logger.error(f"Error updating project: {e}")
                raise

    def archive_project(self, project_id: str, owner_id: str) -> Project:
        """Archive a project"""
        with self._get_db_session() as db:
            try:
                project: Optional[Project] = (
                    db.query(Project)
                    .filter(Project.id == project_id, Project.owner_id == owner_id)
                    .first()
                )
                if not project:
                    raise ValueError(f"Project with id {project_id} not found")

                project.archived_at = datetime.now()
                db.commit()
                db.refresh(project)

                return project
            except Exception as e:
                logger.error(f"Error archiving project: {e}")
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
