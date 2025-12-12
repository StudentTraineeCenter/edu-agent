"""Request schemas for CRUD operations."""

from typing import Optional
from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(..., description="Name of the project")
    description: Optional[str] = Field(None, description="Description of the project")
    language_code: str = Field(default="en", description="Language code for the project")


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Name of the project")
    description: Optional[str] = Field(None, description="Description of the project")
    language_code: Optional[str] = Field(None, description="Language code for the project")


class DocumentCreate(BaseModel):
    file_name: str = Field(..., description="Name of the document file")
    file_type: str = Field(..., description="File extension (pdf, docx, txt, etc.)")
    file_size: int = Field(..., gt=0, description="File size in bytes")
    summary: Optional[str] = Field(None, description="Auto-generated summary of the document")


class DocumentUpdate(BaseModel):
    file_name: Optional[str] = Field(None, description="Name of the document file")
    summary: Optional[str] = Field(None, description="Auto-generated summary of the document")


class ChatCreate(BaseModel):
    title: Optional[str] = Field(None, description="Title of the chat")


class ChatUpdate(BaseModel):
    title: Optional[str] = Field(None, description="Title of the chat")


class NoteCreate(BaseModel):
    title: str = Field(..., description="Title of the note")
    content: str = Field(..., description="Content of the note")
    description: Optional[str] = Field(None, description="Description of the note")


class NoteUpdate(BaseModel):
    title: Optional[str] = Field(None, description="Title of the note")
    content: Optional[str] = Field(None, description="Content of the note")
    description: Optional[str] = Field(None, description="Description of the note")


class QuizCreate(BaseModel):
    name: str = Field(..., description="Name of the quiz")
    description: Optional[str] = Field(None, description="Description of the quiz")


class QuizUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Name of the quiz")
    description: Optional[str] = Field(None, description="Description of the quiz")


class FlashcardGroupCreate(BaseModel):
    name: str = Field(..., description="Name of the flashcard group")
    description: Optional[str] = Field(None, description="Description of the flashcard group")
    study_session_id: Optional[str] = Field(None, description="ID of the study session if this group belongs to one")


class FlashcardGroupUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Name of the flashcard group")
    description: Optional[str] = Field(None, description="Description of the flashcard group")

