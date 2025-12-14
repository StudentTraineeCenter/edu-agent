from datetime import datetime

from pydantic import BaseModel, Field


class NoteDto(BaseModel):

    model_config = {"from_attributes": True}

    id: str = Field(..., description="Unique ID of the note")
    project_id: str = Field(..., description="ID of the project the note belongs to")
    title: str = Field(..., description="Title of the note")
    description: str | None = Field(None, description="Description of the note")
    content: str = Field(..., description="Content of the note")
    created_at: datetime = Field(..., description="Date and time the note was created")
    updated_at: datetime = Field(..., description="Date and time the note was updated")
