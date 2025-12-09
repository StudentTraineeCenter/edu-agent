from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# ============================================================================
# Internal Service Layer Types
# ============================================================================


class MindMapNode(BaseModel):
    """Represents a node in the mind map."""

    id: str = Field(description="Unique identifier for the node")
    label: str = Field(description="Text label for the node")
    position: Dict[str, float] = Field(
        description="Position coordinates {x, y} for the node"
    )
    data: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional data for the node"
    )


class MindMapEdge(BaseModel):
    """Represents an edge (connection) in the mind map."""

    id: str = Field(description="Unique identifier for the edge")
    source: str = Field(description="ID of the source node")
    target: str = Field(description="ID of the target node")
    label: Optional[str] = Field(
        default=None, description="Optional label for the edge"
    )


class MindMapGenerationRequest(BaseModel):
    """Pydantic model for mind map generation request."""

    title: str = Field(description="Title of the mind map")
    description: str = Field(description="Description of the mind map")
    nodes: List[MindMapNode] = Field(description="List of nodes in the mind map")
    edges: List[MindMapEdge] = Field(description="List of edges connecting nodes")


class MindMapGenerationResult(BaseModel):
    """Model for mind map generation result."""

    title: str
    description: str
    map_data: Dict[str, Any]


# ============================================================================
# API Request/Response Types
# ============================================================================


class CreateMindMapRequest(BaseModel):
    """Request model for creating a mind map."""

    custom_instructions: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Custom instructions including topic, format preferences, and any additional context.",
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

    status: str = Field(
        description="Progress status: searching, mapping, building, done"
    )
    message: str = Field(description="Human-readable progress message")
    mind_map_id: Optional[str] = Field(None, description="Mind map ID when done")
    error: Optional[str] = Field(None, description="Error message if failed")
