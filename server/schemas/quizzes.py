from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class QuizDto(BaseModel):
    """Quiz data transfer object."""

    id: str
    project_id: str
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class QuizQuestionDto(BaseModel):
    """Quiz question data transfer object."""

    id: str
    quiz_id: str
    project_id: str
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_option: str
    explanation: Optional[str] = None
    difficulty_level: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CreateQuizRequest(BaseModel):
    """Request model for creating a quiz."""

    question_count: int = Field(
        default=30,
        ge=1,
        le=100,
        description="Number of quiz questions to generate",
    )
    user_prompt: Optional[str] = Field(
        None,
        max_length=2000,
        description="Topic or custom instructions for quiz generation. If provided, will filter documents by topic relevance.",
    )


class UpdateQuizRequest(BaseModel):
    """Request model for updating a quiz."""

    name: Optional[str] = Field(
        None, min_length=1, max_length=255, description="Name of the quiz"
    )
    description: Optional[str] = Field(
        None, max_length=1000, description="Description of the quiz"
    )


class QuizResponse(BaseModel):
    """Response model for quiz operations."""

    quiz: QuizDto
    message: str


class QuizListResponse(BaseModel):
    """Response model for listing quizzes."""

    data: List[QuizDto] = Field(description="List of quizzes")


class QuizQuestionListResponse(BaseModel):
    """Response model for listing quiz questions."""

    data: List[QuizQuestionDto] = Field(description="List of quiz questions")
