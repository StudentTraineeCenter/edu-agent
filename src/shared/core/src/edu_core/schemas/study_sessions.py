from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class StudySessionDto(BaseModel):
    """Study session data transfer object."""

    model_config = {"from_attributes": True}

    id: str = Field(..., description="Unique ID of the study session")
    user_id: str = Field(..., description="ID of the user")
    project_id: str = Field(..., description="ID of the project")
    session_data: dict[str, Any] = Field(..., description="Session data containing flashcards, focus_topics, learning_objectives")
    estimated_time_minutes: int = Field(..., description="Estimated time in minutes")
    session_length_minutes: int = Field(..., description="Requested session length in minutes")
    focus_topics: list[str] | None = Field(None, description="Optional focus topics")
    generated_at: datetime = Field(..., description="Date and time the session was generated")
    started_at: datetime | None = Field(None, description="Date and time the session was started")
    completed_at: datetime | None = Field(None, description="Date and time the session was completed")

