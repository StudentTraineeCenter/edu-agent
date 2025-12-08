from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class CreateMindMapRequest(BaseModel):
    """Request model for creating a mind map."""

    user_prompt: Optional[str] = Field(
        default=None, description="Optional user instructions (topic or focus area)"
    )


class MindMapDto(BaseModel):
    """Mind map data transfer object."""

    id: str
    user_id: str
    project_id: str
    title: str
    description: Optional[str] = None
    map_data: dict[str, Any] = Field(
        description="Structured mind map data (nodes, edges)"
    )
    generated_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MindMapListResponse(BaseModel):
    """Response model for listing mind maps."""

    data: list[MindMapDto]


class MindMapProgressUpdate(BaseModel):
    """Progress update for mind map generation streaming."""

    status: str = Field(description="Progress status: searching, mapping, building, done")
    message: str = Field(description="Human-readable progress message")
    mind_map_id: Optional[str] = Field(None, description="Mind map ID when done")
    error: Optional[str] = Field(None, description="Error message if failed")
