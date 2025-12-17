from datetime import datetime

from pydantic import BaseModel, Field


class FlashcardGroupDto(BaseModel):
    model_config = {"from_attributes": True}

    id: str = Field(..., description="Unique ID of the flashcard group")
    project_id: str = Field(
        ..., description="ID of the project the flashcard group belongs to"
    )
    name: str = Field(..., description="Name of the flashcard group")
    description: str | None = Field(
        None, description="Description of the flashcard group"
    )
    study_session_id: str | None = Field(
        None, description="ID of the study session if this group belongs to one"
    )
    created_at: datetime = Field(
        ..., description="Date and time the flashcard group was created"
    )
    updated_at: datetime = Field(
        ..., description="Date and time the flashcard group was updated"
    )


class FlashcardDto(BaseModel):
    model_config = {"from_attributes": True}

    id: str = Field(..., description="Unique ID of the flashcard")
    group_id: str = Field(..., description="ID of the flashcard group")
    project_id: str = Field(
        ..., description="ID of the project the flashcard belongs to"
    )
    question: str = Field(..., description="Question of the flashcard")
    answer: str = Field(..., description="Answer of the flashcard")
    difficulty_level: str = Field(..., description="Difficulty level of the flashcard")
    position: int = Field(..., description="Position of the flashcard within the group")
    created_at: datetime = Field(
        ..., description="Date and time the flashcard was created"
    )
