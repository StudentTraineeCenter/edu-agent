from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

# ============================================================================
# Internal Service Layer Types
# ============================================================================


class NoteGenerationRequest(BaseModel):
    """Pydantic model for note generation request."""

    title: str = Field(description="Generated title for the note")
    description: str = Field(description="Generated description for the note")
    content: str = Field(description="Generated markdown content for the note")


class NoteGenerationResult(BaseModel):
    """Model for note generation result."""

    title: str
    description: str
    content: str


# ============================================================================
# API Request/Response Types
# ============================================================================


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

    custom_instructions: Optional[str] = Field(
        None,
        max_length=2000,
        description="Custom instructions including topic, format preferences, length, and any additional context.",
    )
    length: Optional[str] = Field(
        None,
        pattern="^(less|normal|more)$",
        description="Length preference: less, normal, or more",
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


class NoteProgressUpdate(BaseModel):
    """Progress update for note generation streaming."""

    status: str = Field(
        description="Progress status: searching, structuring, writing, done"
    )
    message: str = Field(description="Human-readable progress message")
    note_id: Optional[str] = Field(None, description="Note ID when done")
    error: Optional[str] = Field(None, description="Error message if failed")
