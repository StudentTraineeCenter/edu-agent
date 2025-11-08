from enum import Enum


class DocumentStatus(str, Enum):
    """Document processing status enum."""

    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    INDEXED = "indexed"
    FAILED = "failed"

