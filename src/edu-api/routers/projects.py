"""Router for project CRUD operations."""

from auth import get_current_user
from dependencies import get_project_service
from edu_core.exceptions import NotFoundError
from edu_core.schemas.projects import ProjectDto
from edu_core.schemas.users import UserDto
from edu_core.services import ProjectService
from fastapi import APIRouter, Depends, HTTPException

from routers.schemas import ProjectCreate, ProjectUpdate

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])


@router.post("", response_model=ProjectDto, status_code=201)
async def create_project(
    project: ProjectCreate,
    current_user: UserDto = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service),
):
    """Create a new project."""
    try:
        return service.create_project(
            owner_id=current_user.id,
            name=project.name,
            description=project.description,
            language_code=project.language_code,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}", response_model=ProjectDto)
async def get_project(
    project_id: str,
    current_user: UserDto = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service),
):
    """Get a project by ID."""
    try:
        return service.get_project(project_id=project_id, owner_id=current_user.id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=list[ProjectDto])
async def list_projects(
    current_user: UserDto = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service),
):
    """List all projects for a user."""
    try:
        return service.list_projects(owner_id=current_user.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{project_id}", response_model=ProjectDto)
async def update_project(
    project_id: str,
    project: ProjectUpdate,
    current_user: UserDto = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service),
):
    """Update a project."""
    try:
        return service.update_project(
            project_id=project_id,
            owner_id=current_user.id,
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
    current_user: UserDto = Depends(get_current_user),
    service: ProjectService = Depends(get_project_service),
):
    """Delete a project."""
    try:
        service.delete_project(project_id=project_id, owner_id=current_user.id)
        return None
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
