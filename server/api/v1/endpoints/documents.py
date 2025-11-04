from urllib.parse import quote

from api.dependencies import get_data_processing_service, get_document_service, get_user
from core.logger import get_logger
from core.services.data_processing import DataProcessingService
from core.services.documents import DocumentService
from db.models import User
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from schemas.documents import (
    DocumentDto,
    DocumentListResponse,
    DocumentSearchRequest,
    DocumentSearchResponse,
    DocumentUploadResponse,
    SearchResultDto,
)

logger = get_logger(__name__)

router = APIRouter()


@router.post(
    path="/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload documents",
    description="Upload one or more documents for the project. Processing happens asynchronously.",
)
async def upload_document(
    project_id: str,
    files: List[UploadFile] = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    data_processing_service: DataProcessingService = Depends(
        get_data_processing_service
    ),
    current_user: User = Depends(get_user),
):
    """Upload one or more documents and return immediately. Processing happens asynchronously."""
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one file is required",
        )

    logger.info(
        "uploading %d document(s) for project_id=%s", len(files), project_id
    )

    # Validate file types
    allowed_types = ["pdf", "docx", "doc", "txt", "rtf"]
    document_ids = []
    file_contents = []

    for file in files:
        file_extension = (
            file.filename.split(".")[-1].lower() if "." in file.filename else ""
        )

        if file_extension not in allowed_types:
            logger.error("unsupported file_type=%s for file=%s", file_extension, file.filename)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type '{file_extension}' for file '{file.filename}'. Allowed types: {', '.join(allowed_types)}",
            )

    try:
        # Process all files
        for file in files:
            # Read file content
            content = await file.read()

            # Upload document and return immediately
            document_id = data_processing_service.upload_document(
                file_content=content,
                filename=file.filename,
                project_id=project_id,
                owner_id=current_user.id,
            )

            document_ids.append(document_id)
            file_contents.append((document_id, content))

            logger.info(
                "document uploaded document_id=%s, file_name=%s",
                document_id,
                file.filename,
            )

        # Schedule background processing for all documents
        for document_id, content in file_contents:
            background_tasks.add_task(
                data_processing_service.process_document,
                document_id=document_id,
                file_content=content,
                project_id=project_id,
            )

        logger.info(
            "uploaded %d document(s), processing scheduled in background",
            len(document_ids),
        )

        return DocumentUploadResponse(
            document_ids=document_ids,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("error uploading documents: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload documents",
        )


@router.get(
    path="",
    response_model=DocumentListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all documents",
    description="List all documents for a project",
)
def list_documents(
    project_id: str,
    document_service: DocumentService = Depends(get_document_service),
    current_user: User = Depends(get_user),
):
    """List all documents for a project"""
    logger.info("listing documents for project_id=%s", project_id)

    try:
        documents = document_service.list_documents(project_id, current_user.id)

        return DocumentListResponse(
            data=[DocumentDto.model_validate(doc) for doc in documents],
            total_count=len(documents),
        )
    except Exception as e:
        logger.error("error listing documents: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list documents",
        )


@router.get(
    path="/{document_id}",
    response_model=DocumentDto,
    status_code=status.HTTP_200_OK,
    summary="Get a document by id",
    description="Get a document by id",
)
def get_document(
    document_id: str,
    document_service: DocumentService = Depends(get_document_service),
    current_user: User = Depends(get_user),
):
    """Get a document by id"""
    logger.info("getting document_id=%s", document_id)

    try:
        document = document_service.get_document(document_id, current_user.id)

        if not document:
            logger.error("document_id=%s not found", document_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
            )

        return DocumentDto.model_validate(document)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("error getting document: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get document",
        )


@router.post(
    path="/search",
    response_model=DocumentSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Search documents",
    description="Search documents within a project using semantic search",
)
async def search_documents(
    request: DocumentSearchRequest,
    document_service: DocumentService = Depends(get_document_service),
    current_user: User = Depends(get_user),
):
    """Search documents using semantic search with validated typed results."""
    logger.info(
        "searching documents for project_id=%s with query: '%.100s...'",
        request.project_id,
        request.query,
    )

    try:
        results = await document_service.search_documents(
            query=request.query, project_id=request.project_id, top_k=request.top_k
        )

        # Convert to DTOs
        search_results = [
            SearchResultDto(
                citation_index=result.citation_index,
                document_id=result.document_id,
                title=result.title,
                content=result.content,
                score=result.score,
            )
            for result in results
        ]

        return DocumentSearchResponse(
            results=search_results,
            total_count=len(search_results),
            query=request.query,
        )

    except ValueError as e:
        logger.error("validation error in search: %s", e)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error("error searching documents: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search documents",
        )


@router.get(
    path="/{document_id}/preview",
    status_code=status.HTTP_200_OK,
    summary="Preview a document",
    description="Stream document content for preview in browser",
)
def preview_document(
    document_id: str,
    document_service: DocumentService = Depends(get_document_service),
    current_user: User = Depends(get_user),
):
    """Preview a document by streaming its content.

    Supports URL fragment #page=N to navigate to specific page in PDF viewers.

    Example: /v1/documents/{id}/preview#page=5
    """
    logger.info("previewing document_id=%s", document_id)

    try:
        document = document_service.get_document(document_id, current_user.id)

        if not document:
            logger.error("document_id=%s not found", document_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
            )

        # Get blob content as stream
        blob_stream = document_service.get_document_blob_stream(
            document_id, current_user.id
        )

        # Map file extensions to content types
        content_type_map = {
            "pdf": "application/pdf",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "doc": "application/msword",
            "txt": "text/plain",
            "rtf": "application/rtf",
        }

        content_type = content_type_map.get(
            document.file_type.lower(), "application/octet-stream"
        )

        # Encode filename for Content-Disposition header (RFC 5987)
        # This supports Unicode characters
        encoded_filename = quote(document.file_name)

        return StreamingResponse(
            blob_stream,
            media_type=content_type,
            headers={
                "Content-Disposition": f"inline; filename*=UTF-8''{encoded_filename}",
                "Cache-Control": "no-cache",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("error previewing document: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to preview document",
        )
