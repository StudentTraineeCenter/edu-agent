from pydantic import BaseModel, Field

from typing import Literal
from pydantic import BaseModel, Field


class StudyResource(BaseModel):
    id: str = Field(description="ID of the resource (quiz or flashcard)")
    parent_id: str | None = Field(None, description="ID of the parent (e.g. Flashcard Group ID or Quiz ID) for navigation")
    type: Literal["quiz", "flashcard"] = Field(description="Type of the resource")
    title: str = Field(description="Title of the resource")
    description: str | None = Field(None, description="Optional description")


class WeeklyScheduleDay(BaseModel):
    day: str = Field(description="e.g. 'Monday' or 'Day 1'")
    tasks: list[str] = Field(description="List of tasks for the day")


class StudyPlanContent(BaseModel):
    """Schema for structured study plan content."""
    
    analysis: str = Field(description="Brief summary of current performance and analysis.")
    focus_areas: list[str] = Field(description="List of top 3 weak topics or areas to prioritize.")
    action_items: list[StudyResource] = Field(description="Specific recommended actions/resources.")
    schedule: list[WeeklyScheduleDay] = Field(description="Suggested weekly schedule.")
    encouragement: str = Field(description="Encouraging closing message.")
