from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from core.logger import get_logger

from db.model import Project
from db.session import SessionLocal

logger = get_logger(__name__)


class ProjectService:
    def __init__(self):
        pass

    def create_project(
        self, owner_id: str, name: str, description: Optional[str] = None
    ) -> Project:
        """Create a new project"""

        with SessionLocal() as db:
            project = Project(
                id=str(uuid4()),
                owner_id=owner_id,
                name=name,
                description=description,
                created_at=datetime.now(),
                archived_at=None,
            )
            db.add(project)
            db.commit()
            db.refresh(project)
            logger.info(f"Project created: {project.id}")
            return project

    def get_project(self, project_id: str) -> Optional[Project]:
        """Get a project by id"""
        with SessionLocal() as db:
            try:
                project = db.query(Project).filter(Project.id == project_id).first()
                return project
            except Exception as e:
                logger.error(f"Error getting project: {e}")
                raise e

    def list_projects(self, owner_id: str) -> List[Project]:
        """List all projects for a user"""
        with SessionLocal() as db:
            try:
                return db.query(Project).filter(Project.owner_id == owner_id).all()
            except Exception as e:
                logger.error(f"Error listing projects: {e}")
                raise e

    def check_exists(self, owner_id: str, name: str) -> bool:
        """Check if a project exists"""
        with SessionLocal() as db:
            try:
                project = (
                    db.query(Project)
                    .filter(Project.owner_id == owner_id, Project.name == name)
                    .first()
                )
                return project is not None
            except Exception as e:
                logger.error(f"Error checking if project exists: {e}")
                raise e

    def update_project(
        self,
        project_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Project:
        """Update a project"""
        with SessionLocal() as db:
            try:
                project = db.query(Project).filter(Project.id == project_id).first()
                if not project:
                    raise ValueError(f"Project with id {project_id} not found")

                if name is not None:
                    project.name = name
                if description is not None:
                    project.description = description

                db.commit()
                db.refresh(project)
                return project
            except Exception as e:
                logger.error(f"Error updating project: {e}")
                raise e

    def archive_project(self, project_id: str) -> Project:
        """Archive a project"""
        with SessionLocal() as db:
            try:
                project = db.query(Project).filter(Project.id == project_id).first()
                if not project:
                    raise ValueError(f"Project with id {project_id} not found")

                project.archived_at = datetime.now()

                db.commit()
                db.refresh(project)
                return project
            except Exception as e:
                logger.error(f"Error archiving project: {e}")
                raise e
