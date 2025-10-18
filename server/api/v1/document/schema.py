from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class DocumentDto(BaseModel):
    id: str
    owner_id: str
    project_id: Optional[str]
    file_name: str
    file_type: str
    file_size: int
    status: str
    summary: Optional[str]
    uploaded_at: datetime
    processed_at: Optional[datetime]

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    data: List[DocumentDto]
    total_count: int


class DocumentUploadResponse(BaseModel):
    document_id: str
