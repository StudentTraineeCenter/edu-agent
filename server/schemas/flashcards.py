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

    model_config = {"from_attributes": True}


class FlashcardDto(BaseModel):
    """Flashcard data transfer object."""

    id: str
    group_id: str
    project_id: str
    question: str
    answer: str
    difficulty_level: str
    position: int
    created_at: datetime

    model_config = {"from_attributes": True}


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
        description="Topic or custom instructions for flashcard generation. If provided, will filter documents by topic relevance.",
    )
    length: Optional[str] = Field(
        None,
        pattern="^(less|normal|more)$",
        description="Length preference: less, normal, or more",
    )
    difficulty: Optional[str] = Field(
        None,
        pattern="^(easy|medium|hard)$",
        description="Overall difficulty level: easy, medium, or hard",
    )


class UpdateFlashcardGroupRequest(BaseModel):
    """Request model for updating a flashcard group."""

    name: Optional[str] = Field(
        None, min_length=1, max_length=255, description="Name of the flashcard group"
    )
    description: Optional[str] = Field(
        None, max_length=1000, description="Description of the flashcard group"
    )


class CreateFlashcardRequest(BaseModel):
    """Request model for creating a flashcard."""

    question: str = Field(min_length=1, description="Flashcard question")
    answer: str = Field(min_length=1, description="Flashcard answer")
    difficulty_level: str = Field(
        default="medium",
        pattern="^(easy|medium|hard)$",
        description="Difficulty level",
    )
    position: Optional[int] = Field(
        None, ge=0, description="Position for ordering within group"
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


class ReorderFlashcardsRequest(BaseModel):
    """Request model for reordering flashcards."""

    flashcard_ids: List[str] = Field(
        description="List of flashcard IDs in the desired order"
    )


class FlashcardGroupResponse(BaseModel):
    """Response model for flashcard group operations."""

    flashcard_group: FlashcardGroupDto
    message: str


class FlashcardGroupListResponse(BaseModel):
    """Response model for listing flashcard groups."""

    data: List[FlashcardGroupDto] = Field(description="List of flashcard groups")


class FlashcardResponse(BaseModel):
    """Response model for flashcard operations."""

    flashcard: FlashcardDto
    message: str


class FlashcardListResponse(BaseModel):
    """Response model for listing flashcards."""

    data: List[FlashcardDto] = Field(description="List of flashcards")


class FlashcardProgressUpdate(BaseModel):
    """Progress update for flashcard generation streaming."""

    status: str = Field(
        description="Progress status: searching, analyzing, generating, done"
    )
    message: str = Field(description="Human-readable progress message")
    group_id: Optional[str] = Field(None, description="Flashcard group ID when done")
    error: Optional[str] = Field(None, description="Error message if failed")
