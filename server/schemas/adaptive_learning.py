"""Schemas for adaptive learning endpoints."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from schemas.shared import GenerationProgressUpdate


class StudySessionResponse(BaseModel):
    """Response model for study session generation."""

    session_id: str
    flashcard_group_id: Optional[str] = None
    flashcards: List[Dict[str, Any]]
    estimated_time_minutes: int
    focus_topics: List[str]
    learning_objectives: List[str]
    generated_at: str


class StudySessionProgressUpdate(GenerationProgressUpdate):
    """Progress update for study session generation streaming."""

    session_id: Optional[str] = Field(
        None, description="Study session ID when done"
    )
    flashcard_group_id: Optional[str] = Field(
        None, description="Flashcard group ID when done"
    )

