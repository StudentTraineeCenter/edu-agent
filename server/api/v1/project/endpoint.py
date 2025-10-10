from fastapi import APIRouter, status, HTTPException, Response, Depends

from api.v1.project.schema import (
    ProjectCreateRequest,
    ProjectDto,
    ProjectListResponse,
    ProjectUpdateRequest,
)
from api.v1.deps import get_project_service, get_user

from core.logger import get_logger
from core.service.project_service import ProjectService

from db.model import User

logger = get_logger(__name__)

router = APIRouter()


@router.post(
    path="",
    response_model=ProjectDto,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project",
    description="Create a new project",
)
def create_project(
    body: ProjectCreateRequest,
    project_service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(get_user),
):
    """Create a new project"""
    logger.info(f"Creating project: {body.name}")

    exists = project_service.check_exists(current_user.id, body.name)
    if exists:
        logger.error(f"Project with this name already exists: {body.name}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project with this name already exists",
        )

    result = project_service.create_project(
        current_user.id, body.name, body.description, body.language_code
    )

    return ProjectDto.model_validate(result)


@router.get(
    path="",
    response_model=ProjectListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all projects",
    description="List all projects",
)
def list_projects(
    project_service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(get_user),
):
    """List all projects"""
    logger.info(f"Listing projects for owner: {current_user.id}")

    result = project_service.list_projects(current_user.id)

    return ProjectListResponse(
        data=[ProjectDto.model_validate(project) for project in result],
        total_count=len(result),
    )


@router.get(
    path="/{project_id}",
    response_model=ProjectDto,
    status_code=status.HTTP_200_OK,
    summary="Get a project by id",
    description="Get a project by id",
)
def get_project(
    project_id: str,
    project_service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(get_user),
):
    """Get a project by id"""

    logger.info(f"Getting project: {project_id}")

    result = project_service.get_project(project_id, current_user.id)

    if not result:
        logger.error(f"Project not found: {project_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    return ProjectDto.model_validate(result)


@router.put(
    path="/{project_id}",
    response_model=ProjectDto,
    status_code=status.HTTP_200_OK,
    summary="Update a project by id",
    description="Update a project by id",
)
def update_project(
    project_id: str,
    body: ProjectUpdateRequest,
    project_service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(get_user),
):
    """Update a project by id"""
    logger.info(f"Updating project: {project_id}")

    result = project_service.update_project(
        project_id,
        current_user.id,
        body.name,
        body.description,
        body.language_code,
    )
    return ProjectDto.model_validate(result)


@router.post(
    "/{project_id}/archive",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Archive a project by id",
    description="Archive a project by id",
)
def archive_project(
    project_id: str,
    project_service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(get_user),
):
    """Archive a project by id"""
    logger.info(f"Archiving project: {project_id}")
    project_service.archive_project(project_id, current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
