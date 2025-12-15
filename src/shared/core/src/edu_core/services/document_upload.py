"""Service for uploading documents to blob storage."""

from contextlib import contextmanager
from datetime import datetime
from uuid import uuid4

from azure.storage.blob import BlobServiceClient

from edu_core.db.models import Document
from edu_core.db.session import get_session_factory
from edu_core.schemas.documents import DocumentStatus


class DocumentUploadService:
    """Service for uploading documents to blob storage."""

    def __init__(
        self,
        database_url: str,
        azure_storage_connection_string: str,
        azure_storage_input_container_name: str,
    ) -> None:
        """Initialize the document upload service.

        Args:
            database_url: Database connection URL
            azure_storage_connection_string: Azure Storage connection string
            azure_storage_input_container_name: Input container name
        """
        self.database_url = database_url
        self.blob_service_client = BlobServiceClient.from_connection_string(
            azure_storage_connection_string
        )
        self.input_container = azure_storage_input_container_name

    def get_supported_types(self) -> list[str]:
        """Get list of supported document types.

        Returns:
            List of supported file extensions
        """
        return [
            "pdf",
            "tiff",
            "jpg",
            "jpeg",
            "jpe",
            "png",
            "bmp",
            "heif",
            "heic",
            "docx",
            "xlsx",
            "pptx",
            "txt",
            "html",
            "md",
            "rtf",
            "eml",
            "msg",
            "xml",
        ]

    def upload_document(
        self, file_content: bytes, filename: str, project_id: str, owner_id: str
    ) -> str:
        """Upload document to blob storage and create database record.

        Args:
            file_content: The file content as bytes
            filename: Name of the file
            project_id: The project ID
            owner_id: The owner's user ID

        Returns:
            ID of the created document

        Raises:
            Exception: If upload fails
        """
        with self._get_db_session() as db:
            try:
                # Step 1: Create document record
                document_id = self._create_document_record(
                    db=db,
                    file_content=file_content,
                    filename=filename,
                    project_id=project_id,
                    owner_id=owner_id,
                )

                # Step 2: Upload to blob storage
                raw_blob_name = self._upload_to_blob_storage(
                    file_content=file_content,
                    filename=filename,
                    project_id=project_id,
                    document_id=document_id,
                )

                # Step 3: Update document with blob reference
                self._update_document_blob_reference(
                    db=db, document_id=document_id, raw_blob_name=raw_blob_name
                )

                return document_id
            except Exception:
                raise

    def _create_document_record(
        self,
        db,
        file_content: bytes,
        filename: str,
        project_id: str,
        owner_id: str,
    ) -> str:
        """Create initial document record in database.

        Args:
            db: Database session
            file_content: The file content as bytes
            filename: Name of the file
            project_id: The project ID
            owner_id: The owner's user ID

        Returns:
            ID of the created document
        """
        document = Document(
            id=str(uuid4()),
            owner_id=owner_id,
            project_id=project_id,
            file_name=filename,
            file_type=self._get_file_type(filename),
            file_size=len(file_content),
            status=DocumentStatus.UPLOADED.value,
            uploaded_at=datetime.now(),
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        return document.id

    def _upload_to_blob_storage(
        self, file_content: bytes, filename: str, project_id: str, document_id: str
    ) -> str:
        """Upload document to blob storage.

        Args:
            file_content: The file content as bytes
            filename: Name of the file
            project_id: The project ID
            document_id: The document ID

        Returns:
            Blob name where the document was uploaded
        """
        file_extension = self._get_file_type(filename)
        if file_extension != "unknown":
            blob_name = f"{project_id}/{document_id}.{file_extension}"
        else:
            blob_name = f"{project_id}/{document_id}"

        blob_client = self.blob_service_client.get_blob_client(
            container=self.input_container, blob=blob_name
        )
        blob_client.upload_blob(data=file_content, overwrite=True)
        return blob_name

    @staticmethod
    def _get_file_type(filename: str) -> str:
        """Extract file type from filename.

        Args:
            filename: Name of the file

        Returns:
            File extension or 'unknown'
        """
        return filename.split(".")[-1].lower() if "." in filename else "unknown"

    @staticmethod
    def _update_document_blob_reference(
        db, document_id: str, raw_blob_name: str
    ) -> None:
        """Update document with blob reference and set status to processing.

        Args:
            db: Database session
            document_id: The document ID
            raw_blob_name: The blob name in storage
        """
        document = db.query(Document).filter(Document.id == document_id).first()
        if document:
            document.original_blob_name = raw_blob_name
            document.status = DocumentStatus.PROCESSING.value
            db.commit()

    @contextmanager
    def _get_db_session(self):
        """Context manager for database sessions."""
        SessionLocal = get_session_factory()
        db = SessionLocal()
        try:
            yield db
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
