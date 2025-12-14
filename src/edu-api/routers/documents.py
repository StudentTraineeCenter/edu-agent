"""Router for document CRUD operations."""

import asyncio
from typing import List

from fastapi import APIRouter, HTTPException, Depends, File, UploadFile

from auth import get_current_user
from dependencies import (
    get_document_service,
    get_document_upload_service,
    get_queue_service,
    get_usage_service,
)
from edu_shared.services import DocumentUploadService, DocumentService, NotFoundError, UsageService
from edu_shared.schemas.documents import DocumentDto, DocumentStatus
from edu_shared.schemas.queue import QueueTaskMessage, TaskType, DocumentProcessingData
from edu_shared.schemas.users import UserDto
from routers.schemas import DocumentCreate, DocumentUpdate
from edu_shared.services.queue import QueueService

router = APIRouter(prefix="/api/v1/projects/{project_id}/documents", tags=["documents"])


@router.post("/upload", status_code=201)
async def upload_document(
    project_id: str,
    files: List[UploadFile] = File(...),
    current_user: UserDto = Depends(get_current_user),
    upload_service: DocumentUploadService = Depends(get_document_upload_service),
    queue_service: QueueService = Depends(get_queue_service),
    usage_service: UsageService = Depends(get_usage_service),
):
    """Upload one or more documents. Processing happens asynchronously in background."""
    if not files:
        raise HTTPException(status_code=400, detail="At least one file is required")

    # Check usage limit for each file upload
    for _ in files:
        usage_service.check_and_increment(current_user.id, "document_upload")

    # Validate file types
    allowed_types = upload_service.get_supported_types()
    document_ids = []

    for file in files:
        if not file.filename:
            raise HTTPException(
                status_code=400, detail="File with empty filename provided"
            )

        file_extension = (
            file.filename.split(".")[-1].lower() if "." in file.filename else ""
        )

        if file_extension not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type '{file_extension}' for file '{file.filename}'. Allowed types: {', '.join(allowed_types)}",
            )

    try:
        # Read all files concurrently
        async def read_file(file: UploadFile) -> tuple[str, bytes]:
            if not file.filename:
                raise ValueError("File with empty filename provided")
            content = await file.read()
            return file.filename, content

        file_data = await asyncio.gather(*[read_file(file) for file in files])

        # Upload all documents concurrently
        async def upload_single_document(
            filename: str, content: bytes
        ) -> str:
            document_id = await asyncio.to_thread(
                upload_service.upload_document,
                file_content=content,
                filename=filename,
                project_id=project_id,
                owner_id=current_user.id,
            )
            return document_id

        document_ids = await asyncio.gather(
            *[
                upload_single_document(filename, content)
                for filename, content in file_data
            ]
        )

        # Queue processing tasks for all documents
        for document_id in document_ids:
            task_message: QueueTaskMessage = {
                "type": TaskType.DOCUMENT_PROCESSING,
                "data": DocumentProcessingData(
                    document_id=document_id,
                    project_id=project_id,
                    user_id=current_user.id,
                ),
            }
            queue_service.send_message(task_message)

        return {"document_ids": document_ids}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload documents: {str(e)}")


@router.post("", response_model=DocumentDto, status_code=201)
async def create_document(
    project_id: str,
    document: DocumentCreate,
    current_user: UserDto = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
):
    """Create a new document."""
    try:
        return service.create_document(
            owner_id=current_user.id,
            file_name=document.file_name,
            file_type=document.file_type,
            file_size=document.file_size,
            project_id=project_id,
            status=DocumentStatus.UPLOADED,
            summary=document.summary,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}", response_model=DocumentDto)
async def get_document(
    project_id: str,
    document_id: str,
    current_user: UserDto = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
):
    """Get a document by ID."""
    try:
        return service.get_document(document_id=document_id, owner_id=current_user.id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=list[DocumentDto])
async def list_documents(
    project_id: str,
    current_user: UserDto = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
):
    """List all documents for a project."""
    try:
        return service.list_documents(owner_id=current_user.id, project_id=project_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{document_id}", response_model=DocumentDto)
async def update_document(
    project_id: str,
    document_id: str,
    document: DocumentUpdate,
    current_user: UserDto = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
):
    """Update a document."""
    try:
        return service.update_document(
            document_id=document_id,
            owner_id=current_user.id,
            file_name=document.file_name,
            summary=document.summary,
            project_id=project_id,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    project_id: str,
    document_id: str,
    current_user: UserDto = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
):
    """Delete a document."""
    try:
        service.delete_document(document_id=document_id, owner_id=current_user.id)
        return None
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

