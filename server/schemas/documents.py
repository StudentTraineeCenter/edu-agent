from datetime import datetime
from typing import List, Optional

from db.enums import DocumentStatus
from pydantic import BaseModel, Field


class DocumentDto(BaseModel):
    id: str
    owner_id: str
    project_id: Optional[str]
    file_name: str
    file_type: str = Field(..., description="File extension (pdf, docx, txt, etc.)")
    file_size: int = Field(..., gt=0, description="File size in bytes")
    status: DocumentStatus = Field(
        ...,
        description="Document processing status: uploaded, processing, processed, failed, indexed",
    )
    summary: Optional[str] = Field(None, description="Auto-generated summary")
    uploaded_at: datetime
    processed_at: Optional[datetime]

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    data: List[DocumentDto]
    total_count: int = Field(..., ge=0)


class DocumentUploadResponse(BaseModel):
    document_ids: List[str] = Field(..., description="IDs of the uploaded documents")


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
