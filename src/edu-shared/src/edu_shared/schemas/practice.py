from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class PracticeRecordDto(BaseModel):
    """Practice record data transfer object."""

    model_config = {"from_attributes": True}

    id: str = Field(..., description="Unique ID of the practice record")
    user_id: str = Field(..., description="ID of the user")
    project_id: str = Field(..., description="ID of the project")
    item_type: str = Field(..., description="Type of study resource: flashcard or quiz")
    item_id: str = Field(..., description="ID of the study resource (flashcard or quiz question)")
    topic: str = Field(..., description="Topic extracted from question")
    user_answer: Optional[str] = Field(None, description="User's answer (only for quizzes, null for flashcards)")
    correct_answer: str = Field(..., description="The correct answer")
    was_correct: bool = Field(..., description="Whether the user got it right")
    created_at: datetime = Field(..., description="Date and time the practice record was created")

