"""Schemas for search results."""

from pydantic import BaseModel, Field, field_validator


class SearchResultItem(BaseModel):
    """A single search result item with typed fields."""

    id: str = Field(..., description="Unique identifier for the result (segment ID)")
    document_id: str = Field(..., description="ID of the document")
    title: str = Field(..., description="Title of the document")
    content: str = Field(..., description="Relevant content excerpt")

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Content cannot be empty")
        return v

