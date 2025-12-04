from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class PracticeRecordDto(BaseModel):
    """Practice record data transfer object."""

    id: str
    user_id: str
    project_id: str
    item_type: str  # "flashcard" or "quiz" - type of study resource
    item_id: str  # flashcard_id or quiz_question_id - ID of the study resource
    topic: str
    user_answer: Optional[str] = None  # Only for quizzes, null for flashcards
    correct_answer: str
    was_correct: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class CreatePracticeRecordRequest(BaseModel):
    """Request model for creating a practice record."""

    item_type: str = Field(
        ..., pattern="^(flashcard|quiz)$", description="Type of study resource: flashcard or quiz"
    )
    item_id: str = Field(..., description="ID of the study resource (flashcard or quiz question)")
    topic: str = Field(..., max_length=500, description="Topic extracted from question")
    user_answer: Optional[str] = Field(
        None, description="User's answer (only for quizzes, null for flashcards)"
    )
    correct_answer: str = Field(
        ...,
        description="The correct answer - flashcard answer or quiz correct option",
    )
    was_correct: bool = Field(..., description="Whether the user got it right")
    quality_rating: Optional[int] = Field(
        None,
        ge=0,
        le=5,
        description="Quality rating for spaced repetition (0-5). Only for flashcards with SR enabled."
    )


class CreatePracticeRecordBatchRequest(BaseModel):
    """Request model for creating multiple practice records."""

    practice_records: List[CreatePracticeRecordRequest] = Field(
        ..., min_items=1, max_items=100, description="List of practice records to create"
    )


class PracticeRecordResponse(BaseModel):
    """Response model for practice record operations."""

    practice_record: PracticeRecordDto
    message: str


class PracticeRecordListResponse(BaseModel):
    """Response model for listing practice records."""

    data: List[PracticeRecordDto] = Field(description="List of practice records")

