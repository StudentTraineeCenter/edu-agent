from fastapi import APIRouter, status, HTTPException, UploadFile, File, Depends

from api.v1.document.schema import (
    DocumentUploadResponse,
    DocumentListResponse,
    DocumentDto,
)
from api.v1.deps import get_document_service

from core.logger import get_logger
from core.service.document_service import DocumentService

logger = get_logger(__name__)

router = APIRouter()


@router.post(
    path="/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a document",
    description="Upload and process a document for the project",
)
async def upload_document(
    project_id: str,
    owner_id: str,
    file: UploadFile = File(...),
    document_service: DocumentService = Depends(get_document_service),
):
    """Upload and process a document"""
    logger.info(f"Uploading document: {file.filename} for project: {project_id}")

    # Validate file type
    allowed_types = ["pdf", "docx", "doc", "txt", "rtf"]
    file_extension = (
        file.filename.split(".")[-1].lower() if "." in file.filename else ""
    )

    if file_extension not in allowed_types:
        logger.error(f"Unsupported file type: {file_extension}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed types: {', '.join(allowed_types)}",
        )

    try:
        # Read file content
        content = await file.read()

        # Process document
        document_id = await document_service.upload_document(
            file_content=content,
            filename=file.filename,
            project_id=project_id,
            owner_id=owner_id,
        )

        return DocumentUploadResponse(
            document_id=document_id,
            file_name=file.filename,
            message="Document uploaded and processed",
        )

    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload and process document",
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
    owner_id: str,
    document_service: DocumentService = Depends(get_document_service),
):
    """List all documents for a project"""
    logger.info(f"Listing documents for project: {project_id}, owner: {owner_id}")

    try:
        documents = document_service.list_documents(project_id, owner_id)

        return DocumentListResponse(
            data=[DocumentDto.model_validate(doc) for doc in documents],
            total_count=len(documents),
        )
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
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
):
    """Get a document by id"""
    logger.info(f"Getting document: {document_id}")

    try:
        document = document_service.get_document(document_id)

        if not document:
            logger.error(f"Document not found: {document_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
            )

        return DocumentDto.model_validate(document)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get document",
        )
