from datetime import datetime
from pydantic import BaseModel, Field


from edu_core.schemas.study_plan_generation import StudyPlanContent

class StudyPlanDto(BaseModel):
    """Study plan data transfer object."""

    model_config = {"from_attributes": True}

    id: str = Field(..., description="Unique ID of the plan")
    user_id: str = Field(..., description="ID of the user")
    project_id: str = Field(..., description="ID of the project")
    content: StudyPlanContent = Field(..., description="Structured content of the study plan")
    weak_topics: list[str] = Field(
        default_factory=list, description="List of weak topics identified"
    )
    created_at: datetime = Field(..., description="Date created")
