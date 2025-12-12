"""Router for project CRUD operations."""

from fastapi import APIRouter, HTTPException, Depends

from auth import get_current_user
from edu_shared.services import ProjectService, NotFoundError
from edu_shared.schemas.projects import ProjectDto
from edu_shared.schemas.users import UserDto
from routers.schemas import ProjectCreate, ProjectUpdate

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])


@router.post("", response_model=ProjectDto, status_code=201)
async def create_project(
    project: ProjectCreate,
    current_user: UserDto = Depends(get_current_user),
):
    """Create a new project."""
    service = ProjectService()
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
):
    """Get a project by ID."""
    service = ProjectService()
    try:
        return service.get_project(project_id=project_id, owner_id=current_user.id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=list[ProjectDto])
async def list_projects(
    current_user: UserDto = Depends(get_current_user),
):
    """List all projects for a user."""
    service = ProjectService()
    try:
        return service.list_projects(owner_id=current_user.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{project_id}", response_model=ProjectDto)
async def update_project(
    project_id: str,
    project: ProjectUpdate,
    current_user: UserDto = Depends(get_current_user),
):
    """Update a project."""
    service = ProjectService()
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
):
    """Delete a project."""
    service = ProjectService()
    try:
        service.delete_project(project_id=project_id, owner_id=current_user.id)
        return None
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

