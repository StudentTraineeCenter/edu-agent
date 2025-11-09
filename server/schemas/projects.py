from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ProjectCreateRequest(BaseModel):
    """Request model for creating a new project."""

    name: str = Field(description="Name of the project")
    description: Optional[str] = Field(None, description="Description of the project")
    language_code: Optional[str] = Field(
        "en", description="Language code (e.g., 'en', 'es', 'fr')"
    )


class ProjectUpdateRequest(BaseModel):
    """Request model for updating a project."""

    name: Optional[str] = Field(None, description="Name of the project")
    description: Optional[str] = Field(None, description="Description of the project")
    language_code: Optional[str] = Field(
        None, description="Language code (e.g., 'en', 'es', 'fr')"
    )


class ProjectDto(BaseModel):
    """Response model for project data."""

    model_config = {"from_attributes": True}

    id: str = Field(description="Unique ID of the project")
    owner_id: str = Field(description="ID of the project owner")
    name: str = Field(description="Name of the project")
    description: Optional[str] = Field(description="Description of the project")
    language_code: str = Field(description="Language code")
    created_at: datetime = Field(description="Creation timestamp")


class ProjectListResponse(BaseModel):
    """Response model for listing projects."""

    data: List[ProjectDto] = Field(description="List of projects")
