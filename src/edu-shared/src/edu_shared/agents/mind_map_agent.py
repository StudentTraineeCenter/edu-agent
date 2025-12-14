
from edu_shared.agents.base import BaseContentAgent
from pydantic import BaseModel, Field


class MindMapNodeData(BaseModel):
    """Model for a mind map node."""

    id: str = Field(..., description="Unique identifier for the node")
    label: str = Field(..., description="Text label for the node")
    position: dict[str, float] = Field(
        ..., description="Position coordinates {x, y} for the node"
    )
    data: dict = Field(
        default_factory=dict, description="Additional data for the node"
    )


class MindMapEdgeData(BaseModel):
    """Model for a mind map edge."""

    id: str = Field(..., description="Unique identifier for the edge")
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    label: str | None = Field(
        default=None, description="Optional label for the edge"
    )


class MindMapGenerationResult(BaseModel):
    """Model for mind map generation result."""

    title: str = Field(..., description="The title of the mind map")
    description: str = Field(..., description="The description of the mind map")
    nodes: list[MindMapNodeData] = Field(..., description="List of nodes in the mind map")
    edges: list[MindMapEdgeData] = Field(..., description="List of edges in the mind map")


class MindMapAgent(BaseContentAgent[MindMapGenerationResult]):
    @property
    def output_model(self):
        return MindMapGenerationResult

    @property
    def prompt_template(self):
        return "mind_map_prompt"
