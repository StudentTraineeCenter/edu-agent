from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class StudyPlanDto(BaseModel):
    """Study plan data transfer object."""

    id: str
    user_id: str
    project_id: str
    title: str
    description: Optional[str] = None
    plan_content: dict[str, Any] = Field(description="Structured plan content (JSON)")
    generated_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
