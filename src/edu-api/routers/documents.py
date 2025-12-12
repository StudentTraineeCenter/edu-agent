"""Router for document CRUD operations."""

import asyncio
from typing import List

from fastapi import APIRouter, HTTPException, Header, File, UploadFile

from edu_shared.services import DocumentService, DocumentProcessingService, NotFoundError
from edu_shared.schemas.documents import DocumentDto, DocumentStatus
from edu_shared.schemas.queue import QueueTaskMessage, TaskType, DocumentProcessingData
from routers.schemas import DocumentCreate, DocumentUpdate
from services.queue import QueueService
from config import get_settings

router = APIRouter(prefix="/api/v1/projects/{project_id}/documents", tags=["documents"])


@router.post("/upload", status_code=201)
async def upload_document(
    project_id: str,
    files: List[UploadFile] = File(...),
    user_id: str = Header(..., alias="X-User-Id"),
):
    """Upload one or more documents. Processing happens asynchronously in background."""
    if not files:
        raise HTTPException(status_code=400, detail="At least one file is required")

    settings = get_settings()
    
    # Initialize services
    # Note: For upload, we only need blob storage and database access
    # The CU client and embeddings are only needed for processing (done in worker)
    processing_service = DocumentProcessingService(
        database_url=settings.database_url,
        azure_storage_connection_string=settings.azure_storage_connection_string,
        azure_storage_input_container_name=settings.azure_storage_input_container_name,
        azure_storage_output_container_name=settings.azure_storage_output_container_name,
        azure_cu_endpoint="",
        azure_cu_key="",
        azure_cu_analyzer_id="",
        azure_openai_embedding_deployment="",  # Not used in upload
        azure_openai_endpoint="",  # Not used in upload
        azure_openai_api_version="",  # Not used in upload
    )
    
    queue_service = QueueService(
        connection_string=settings.azure_storage_connection_string,
        queue_name=settings.azure_storage_queue_name,
    )

    # Validate file types
    allowed_types = processing_service.get_supported_types()
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
        ) -> tuple[str, bytes]:
            document_id = await asyncio.to_thread(
                processing_service.upload_document,
                file_content=content,
                filename=filename,
                project_id=project_id,
                owner_id=user_id,
            )
            return document_id, content

        upload_results = await asyncio.gather(
            *[
                upload_single_document(filename, content)
                for filename, content in file_data
            ]
        )

        document_ids = [doc_id for doc_id, _ in upload_results]
        file_contents = upload_results

        # Queue processing tasks for all documents
        for document_id, content in file_contents:
            task_message: QueueTaskMessage = {
                "type": TaskType.DOCUMENT_PROCESSING,
                "data": DocumentProcessingData(
                    document_id=document_id,
                    project_id=project_id,
                    user_id=user_id,
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
    user_id: str = Header(..., alias="X-User-Id"),
):
    """Create a new document."""
    service = DocumentService()
    try:
        return service.create_document(
            owner_id=user_id,
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
    user_id: str = Header(..., alias="X-User-Id"),
):
    """Get a document by ID."""
    service = DocumentService()
    try:
        return service.get_document(document_id=document_id, owner_id=user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=list[DocumentDto])
async def list_documents(
    project_id: str,
    user_id: str = Header(..., alias="X-User-Id"),
):
    """List all documents for a project."""
    service = DocumentService()
    try:
        return service.list_documents(owner_id=user_id, project_id=project_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{document_id}", response_model=DocumentDto)
async def update_document(
    project_id: str,
    document_id: str,
    document: DocumentUpdate,
    user_id: str = Header(..., alias="X-User-Id"),
):
    """Update a document."""
    service = DocumentService()
    try:
        return service.update_document(
            document_id=document_id,
            owner_id=user_id,
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
    user_id: str = Header(..., alias="X-User-Id"),
):
    """Delete a document."""
    service = DocumentService()
    try:
        service.delete_document(document_id=document_id, owner_id=user_id)
        return None
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

