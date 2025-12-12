from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


class MindMapDto(BaseModel):
    """Mind map data transfer object."""

    model_config = {"from_attributes": True}

    id: str = Field(..., description="Unique ID of the mind map")
    user_id: str = Field(..., description="ID of the user")
    project_id: str = Field(..., description="ID of the project")
    title: str = Field(..., description="Title of the mind map")
    description: Optional[str] = Field(None, description="Description of the mind map")
    map_data: dict[str, Any] = Field(..., description="Structured mind map data (nodes, edges)")
    generated_at: datetime = Field(..., description="Date and time the mind map was generated")
    updated_at: datetime = Field(..., description="Date and time the mind map was updated")

