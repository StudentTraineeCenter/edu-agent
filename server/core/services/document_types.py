"""Typed models for document service to ensure type safety and validation."""

from typing import Optional

from pydantic import BaseModel, Field, field_validator


class DocumentMetadata(BaseModel):
    """Metadata stored with each document segment in the vector store."""

    segment_id: str = Field(..., description="ID for the document segment")
    document_id: str = Field(..., description="ID of the parent document")
    title: Optional[str] = Field(None, description="Title of the document")
    score: Optional[float] = Field(None, description="Similarity score")

    @field_validator("score")
    @classmethod
    def validate_score(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (0.0 <= v <= 1.0):
            raise ValueError("Score must be between 0.0 and 1.0")
        return v


class SearchResultItem(BaseModel):
    """A single search result item with typed fields."""

    citation_index: int = Field(
        ..., ge=1, description="Citation number for referencing"
    )
    document_id: str = Field(..., description="ID of the document")
    title: str = Field(..., description="Title of the document")
    content: str = Field(..., description="Relevant content excerpt")
    score: float = Field(..., ge=0.0, le=1.0, description="Relevance score (0-1)")

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Content cannot be empty")
        return v


class ContextSource(BaseModel):
    """Source information for RAG context."""

    id: str = Field(..., description="Segment ID")
    citation_index: int = Field(..., ge=1, description="Citation number")
    title: str = Field(..., description="Document title")
    document_id: str = Field(..., description="Parent document ID")
    content: str = Field(..., description="Content excerpt")
    preview_url: Optional[str] = Field(None, description="URL to preview document")
    score: float = Field(default=1.0, ge=0.0, le=1.0, description="Relevance score")


class SearchResponse(BaseModel):
    """Typed response for document search operations."""

    results: list[SearchResultItem] = Field(default_factory=list)
    total_count: int = Field(..., ge=0, description="Total number of results")
    query: str = Field(..., description="Original search query")

    @field_validator("total_count")
    @classmethod
    def validate_total_count(cls, v: int, info) -> int:
        results = info.data.get("results", [])
        if v < len(results):
            raise ValueError("total_count cannot be less than number of results")
        return v
