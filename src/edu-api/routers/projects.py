"""Router for project CRUD operations."""

from fastapi import APIRouter, HTTPException, Header
from typing import Optional

from edu_shared.services import ProjectService, NotFoundError
from edu_shared.schemas.projects import ProjectDto
from routers.schemas import ProjectCreate, ProjectUpdate

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])


def get_user_id(x_user_id: Optional[str] = Header(None, alias="X-User-Id")) -> str:
    """Extract user ID from header."""
    if not x_user_id:
        raise HTTPException(status_code=401, detail="X-User-Id header is required")
    return x_user_id


@router.post("", response_model=ProjectDto, status_code=201)
async def create_project(
    project: ProjectCreate,
    user_id: str = Header(..., alias="X-User-Id"),
):
    """Create a new project."""
    service = ProjectService()
    try:
        return service.create_project(
            owner_id=user_id,
            name=project.name,
            description=project.description,
            language_code=project.language_code,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}", response_model=ProjectDto)
async def get_project(
    project_id: str,
    user_id: str = Header(..., alias="X-User-Id"),
):
    """Get a project by ID."""
    service = ProjectService()
    try:
        return service.get_project(project_id=project_id, owner_id=user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=list[ProjectDto])
async def list_projects(
    user_id: str = Header(..., alias="X-User-Id"),
):
    """List all projects for a user."""
    service = ProjectService()
    try:
        return service.list_projects(owner_id=user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{project_id}", response_model=ProjectDto)
async def update_project(
    project_id: str,
    project: ProjectUpdate,
    user_id: str = Header(..., alias="X-User-Id"),
):
    """Update a project."""
    service = ProjectService()
    try:
        return service.update_project(
            project_id=project_id,
            owner_id=user_id,
            name=project.name,
            description=project.description,
            language_code=project.language_code,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: str,
    user_id: str = Header(..., alias="X-User-Id"),
):
    """Delete a project."""
    service = ProjectService()
    try:
        service.delete_project(project_id=project_id, owner_id=user_id)
        return None
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

