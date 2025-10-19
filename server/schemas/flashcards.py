from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class FlashcardGroupDto(BaseModel):
    """Flashcard group data transfer object."""

    id: str
    project_id: str
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FlashcardDto(BaseModel):
    """Flashcard data transfer object."""

    id: str
    group_id: str
    project_id: str
    question: str
    answer: str
    difficulty_level: str
    created_at: datetime

    class Config:
        from_attributes = True


class CreateFlashcardGroupRequest(BaseModel):
    """Request model for creating a flashcard group."""

    flashcard_count: int = Field(
        default=30,
        ge=1,
        le=100,
        description="Number of flashcards to generate",
    )
    user_prompt: Optional[str] = Field(
        None,
        max_length=2000,
        description="Custom prompt to enhance generation",
    )


class UpdateFlashcardGroupRequest(BaseModel):
    """Request model for updating a flashcard group."""

    name: Optional[str] = Field(
        None, min_length=1, max_length=255, description="Name of the flashcard group"
    )
    description: Optional[str] = Field(
        None, max_length=1000, description="Description of the flashcard group"
    )


class UpdateFlashcardRequest(BaseModel):
    """Request model for updating a flashcard."""

    question: Optional[str] = Field(
        None, min_length=1, description="Flashcard question"
    )
    answer: Optional[str] = Field(None, min_length=1, description="Flashcard answer")
    difficulty_level: Optional[str] = Field(
        None, pattern="^(easy|medium|hard)$", description="Difficulty level"
    )


class FlashcardGroupResponse(BaseModel):
    """Response model for flashcard group operations."""

    flashcard_group: FlashcardGroupDto
    message: str


class FlashcardGroupListResponse(BaseModel):
    """Response model for listing flashcard groups."""

    data: List[FlashcardGroupDto]
    total: int


class FlashcardResponse(BaseModel):
    """Response model for flashcard operations."""

    flashcard: FlashcardDto
    message: str


class FlashcardListResponse(BaseModel):
    """Response model for listing flashcards."""

    flashcards: List[FlashcardDto]
    total: int
