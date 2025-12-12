from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class DocumentStatus(str, Enum):
    """Document processing status enum."""

    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    INDEXED = "indexed"
    FAILED = "failed"


class DocumentDto(BaseModel):
    
    model_config = {"from_attributes": True}

    id: str = Field(..., description="Unique ID of the document")
    owner_id: str = Field(..., description="ID of the document owner")
    project_id: Optional[str] = Field(None, description="ID of the project the document belongs to")
    file_name: str = Field(..., description="Name of the document file")
    file_type: str = Field(..., description="File extension (pdf, docx, txt, etc.)")
    file_size: int = Field(..., gt=0, description="File size in bytes")
    status: DocumentStatus = Field(..., description="Document processing status: uploaded, processing, processed, failed, indexed")
    summary: Optional[str] = Field(None, description="Auto-generated summary of the document")
    uploaded_at: datetime = Field(..., description="Date and time the document was uploaded")
    processed_at: Optional[datetime] = Field(None, description="Date and time the document was processed")
