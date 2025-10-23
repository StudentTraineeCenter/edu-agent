from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class DocumentDto(BaseModel):
    id: str
    owner_id: str
    project_id: Optional[str]
    file_name: str
    file_type: str = Field(..., description="File extension (pdf, docx, txt, etc.)")
    file_size: int = Field(..., gt=0, description="File size in bytes")
    status: str = Field(
        ...,
        description="Document processing status: uploaded, processing, processed, failed, indexed",
    )
    summary: Optional[str] = Field(None, description="Auto-generated summary")
    uploaded_at: datetime
    processed_at: Optional[datetime]

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed_statuses = ["uploaded", "processing", "processed", "failed", "indexed"]
        if v not in allowed_statuses:
            raise ValueError(
                f"Status must be one of: {', '.join(allowed_statuses)}, got: {v}"
            )
        return v

    @field_validator("file_type")
    @classmethod
    def validate_file_type(cls, v: str) -> str:
        allowed_types = ["pdf", "docx", "doc", "txt", "rtf"]
        if v.lower() not in allowed_types:
            raise ValueError(
                f"File type must be one of: {', '.join(allowed_types)}, got: {v}"
            )
        return v.lower()

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    data: List[DocumentDto]
    total_count: int = Field(..., ge=0)

    @field_validator("total_count")
    @classmethod
    def validate_total_count(cls, v: int, info) -> int:
        data = info.data.get("data", [])
        if v < len(data):
            raise ValueError("total_count cannot be less than number of items in data")
        return v


class DocumentUploadResponse(BaseModel):
    document_id: str = Field(..., description="ID of the uploaded document")


class DocumentSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query")
    project_id: str = Field(..., description="Project ID to search within")
    top_k: int = Field(
        default=5, ge=1, le=50, description="Number of results to return"
    )


class DocumentSearchResponse(BaseModel):
    results: List["SearchResultDto"]
    total_count: int = Field(..., ge=0)
    query: str


class SearchResultDto(BaseModel):
    citation_index: int = Field(..., ge=1, description="Citation number")
    document_id: str = Field(..., description="Document ID")
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Relevant content excerpt")
    score: float = Field(..., ge=0.0, le=1.0, description="Relevance score")
