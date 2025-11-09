from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class AttemptDto(BaseModel):
    """Attempt data transfer object."""

    id: str
    user_id: str
    project_id: str
    item_type: str  # "flashcard" or "quiz"
    item_id: str  # flashcard_id or quiz_question_id
    topic: str
    user_answer: Optional[str] = None  # Only for quizzes, null for flashcards
    correct_answer: str
    was_correct: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class CreateAttemptRequest(BaseModel):
    """Request model for creating an attempt record."""

    item_type: str = Field(
        ..., pattern="^(flashcard|quiz)$", description="Type of item: flashcard or quiz"
    )
    item_id: str = Field(..., description="ID of the flashcard or quiz question")
    topic: str = Field(..., max_length=500, description="Topic extracted from question")
    user_answer: Optional[str] = Field(
        None, description="User's answer (only for quizzes, null for flashcards)"
    )
    correct_answer: str = Field(
        ...,
        description="The correct answer - flashcard answer or quiz correct option",
    )
    was_correct: bool = Field(..., description="Whether the user got it right")


class CreateAttemptBatchRequest(BaseModel):
    """Request model for creating multiple attempt records."""

    attempts: List[CreateAttemptRequest] = Field(
        ..., min_items=1, max_items=100, description="List of attempts to create"
    )


class AttemptResponse(BaseModel):
    """Response model for attempt operations."""

    attempt: AttemptDto
    message: str


class AttemptListResponse(BaseModel):
    """Response model for listing attempts."""

    data: List[AttemptDto] = Field(description="List of attempts")
