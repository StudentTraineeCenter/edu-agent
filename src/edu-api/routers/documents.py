"""Router for document CRUD operations."""

from fastapi import APIRouter, HTTPException, Header

from edu_shared.services import DocumentService, NotFoundError
from edu_shared.schemas.documents import DocumentDto, DocumentStatus
from routers.schemas import DocumentCreate, DocumentUpdate

router = APIRouter(prefix="/api/v1/projects/{project_id}/documents", tags=["documents"])


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

