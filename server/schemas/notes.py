from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class NoteDto(BaseModel):
    """Note data transfer object."""

    id: str
    project_id: str
    title: str
    description: Optional[str] = None
    content: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CreateNoteRequest(BaseModel):
    """Request model for creating a note."""

    user_prompt: Optional[str] = Field(
        None,
        max_length=2000,
        description="Topic or custom instructions for note generation. If provided, will filter documents by topic relevance.",
    )


class UpdateNoteRequest(BaseModel):
    """Request model for updating a note."""

    title: Optional[str] = Field(
        None, min_length=1, max_length=255, description="Title of the note"
    )
    description: Optional[str] = Field(
        None, max_length=1000, description="Description of the note"
    )
    content: Optional[str] = Field(
        None, min_length=1, description="Markdown content of the note"
    )


class NoteResponse(BaseModel):
    """Response model for note operations."""

    note: NoteDto
    message: str


class NoteListResponse(BaseModel):
    """Response model for listing notes."""

    data: List[NoteDto] = Field(description="List of notes")

