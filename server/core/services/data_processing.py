"""Service for processing documents with Azure Content Understanding."""

import asyncio
import uuid
from contextlib import contextmanager
from datetime import datetime
from typing import Optional

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure.storage.blob import BlobServiceClient
from langchain_openai import AzureOpenAIEmbeddings
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)
from sqlalchemy.orm import Session

from core.agents.llm import make_embeddings
from core.config import app_config
from core.logger import get_logger
from core.services.content_understanding import AzureContentUnderstandingClient
from db.enums import DocumentStatus
from db.models import Document, DocumentSegment
from db.session import SessionLocal
from schemas.documents import DocumentAnalysisResult

logger = get_logger(__name__)


class DataProcessingService:
    """Service for processing documents with Azure Content Understanding."""

    def __init__(self) -> None:
        """Initialize the data processing service."""
        self.blob_service_client = BlobServiceClient.from_connection_string(
            app_config.AZURE_STORAGE_CONNECTION_STRING
        )

        self.cu_client = AzureContentUnderstandingClient(
            endpoint=app_config.AZURE_CU_ENDPOINT,
            subscription_key=app_config.AZURE_CU_KEY,
        )

        self.embeddings = make_embeddings()

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
        """Upload document to blob storage and return immediately.

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
                logger.info(
                    f"uploading document file_name={filename} for project_id={project_id} by owner_id={owner_id}"
                )

                # Step 1: Create document record
                document_id = self._create_document_record(
                    db=db,
                    file_content=file_content,
                    filename=filename,
                    project_id=project_id,
                    owner_id=owner_id,
                )
                logger.info_structured("created document record", document_id=document_id, project_id=project_id)

                # Step 2: Upload to blob storage
                raw_blob_name = self._upload_to_blob_storage(
                    file_content=file_content,
                    filename=filename,
                    project_id=project_id,
                    document_id=document_id,
                )
                logger.info(
                    f"uploaded document to blob storage blob_name={raw_blob_name}"
                )

                # Step 3: Update document with blob reference
                self._update_document_blob_reference(
                    db=db, document_id=document_id, raw_blob_name=raw_blob_name
                )
                logger.info(
                    f"updated document with blob reference document_id={document_id}"
                )

                return document_id
            except Exception as e:
                logger.error_structured("error uploading document", filename=filename, project_id=project_id, error=str(e), exc_info=True)
                raise

    async def process_document(
        self, document_id: str, file_content: bytes, project_id: str
    ) -> None:
        """Process document asynchronously: analyze, index, and create embeddings.

        Args:
            document_id: The document ID
            file_content: The file content as bytes
            project_id: The project ID

        Raises:
            Exception: If processing fails
        """
        with self._get_db_session() as db:
            try:
                logger.info_structured("starting document processing", document_id=document_id, project_id=project_id)

                # Step 1: Extract text using Content Understanding (run in thread pool to avoid blocking)
                analyzed_result = await asyncio.to_thread(
                    self._analyze_document, file_content=file_content
                )
                analyzed_content = analyzed_result.content
                analyzed_summary = analyzed_result.summary

                # Step 2: Move blob from input to output and create contents.txt (run in thread pool to avoid blocking)
                await asyncio.to_thread(
                    self._move_blob_to_output,
                    content=analyzed_content,
                    project_id=project_id,
                    document_id=document_id,
                    db=db,
                )
                logger.info(
                    f"moved blob to output and created contents.txt for document_id={document_id}"
                )

                # Step 3: Update document status to processed
                self._update_document_processed_status(
                    db=db,
                    document_id=document_id,
                    summary=analyzed_summary,
                )
                logger.info(
                    f"updated document status to processed document_id={document_id}"
                )

                # Step 4: Create segments and embeddings
                await self._create_segments_and_embeddings(
                    db=db, document_id=document_id, content=analyzed_content
                )
                logger.info(
                    f"created segments and embeddings document_id={document_id}"
                )

                # Step 5: Mark document as indexed
                self._mark_document_indexed(db=db, document_id=document_id)
                logger.info_structured("document successfully indexed", document_id=document_id, project_id=project_id)
            except Exception as e:
                logger.error_structured("error processing document", document_id=document_id, project_id=project_id, error=str(e), exc_info=True)
                self._mark_document_failed(db=db, document_id=document_id)
                raise

    async def process(
        self, file_content: bytes, filename: str, project_id: str, owner_id: str
    ) -> str:
        """Upload document to blob storage and trigger indexing (synchronous version for backward compatibility).

        Args:
            file_content: The file content as bytes
            filename: Name of the file
            project_id: The project ID
            owner_id: The owner's user ID

        Returns:
            ID of the created document
        """
        document_id = self.upload_document(
            file_content=file_content,
            filename=filename,
            project_id=project_id,
            owner_id=owner_id,
        )
        await self.process_document(
            document_id=document_id,
            file_content=file_content,
            project_id=project_id,
        )
        return document_id

    def _create_document_record(
        self,
        db: Session,
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
            id=str(uuid.uuid4()),
            owner_id=owner_id,
            project_id=project_id,
            file_name=filename,
            file_type=self._get_file_type(filename),
            file_size=len(file_content),
            status=DocumentStatus.UPLOADED,
            uploaded_at=datetime.now(),
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        logger.info(
            f"created document record document_id={document.id} (file_name={filename}, size={len(file_content)} bytes)"
        )
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
        # Extract file extension
        file_extension = self._get_file_type(filename)
        if file_extension != "unknown":
            blob_name = f"{project_id}/{document_id}.{file_extension}"
        else:
            blob_name = f"{project_id}/{document_id}"

        blob_client = self.blob_service_client.get_blob_client(
            container=app_config.AZURE_STORAGE_INPUT_CONTAINER_NAME, blob=blob_name
        )
        blob_client.upload_blob(data=file_content, overwrite=True)
        logger.info_structured("document uploaded to blob storage", blob_name=blob_name)
        return blob_name

    def _analyze_document(self, file_content: bytes) -> DocumentAnalysisResult:
        """Analyze document using Azure Content Understanding.

        Args:
            file_content: The file content as bytes

        Returns:
            DocumentAnalysisResult containing content and summary
        """
        response = self.cu_client.begin_analyze_data(
            analyzer_id=app_config.AZURE_CU_ANALYZER_ID, data=file_content
        )
        result = self.cu_client.poll_result(response=response)

        contents_item = result["result"]["contents"][0]

        content = contents_item["markdown"]
        summary = contents_item["fields"]["Summary"]["valueString"]

        return DocumentAnalysisResult(
            content=content,
            summary=summary,
        )

    def _move_blob_to_output(
        self, content: str, project_id: str, document_id: str, db: Session
    ) -> None:
        """Move original blob from input to output and create processed contents file.

        Creates contents.txt file but does not use it for blob operations.

        Args:
            content: The processed content
            project_id: The project ID
            document_id: The document ID
            db: Database session
        """
        # Get document to access file_type
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise ValueError(f"Document {document_id} not found")

        # Construct blob paths from project_id and document_id
        file_extension = document.file_type if document.file_type != "unknown" else ""
        if file_extension:
            original_blob_name = f"{project_id}/{document_id}.{file_extension}"
        else:
            original_blob_name = f"{project_id}/{document_id}"

        contents_blob_name = f"{project_id}/{document_id}.contents.txt"

        # Step 1: Copy original blob from input to output container (preserve original file)
        input_blob_client = self.blob_service_client.get_blob_client(
            container=app_config.AZURE_STORAGE_INPUT_CONTAINER_NAME,
            blob=original_blob_name,
        )
        output_blob_client = self.blob_service_client.get_blob_client(
            container=app_config.AZURE_STORAGE_OUTPUT_CONTAINER_NAME,
            blob=original_blob_name,
        )

        # Download from input and upload to output to copy the blob
        blob_data = input_blob_client.download_blob().readall()
        output_blob_client.upload_blob(blob_data, overwrite=True)
        logger.info_structured("copied original blob to output", blob_name=original_blob_name)

        # Step 2: Create contents.txt file with processed content
        contents_blob_client = self.blob_service_client.get_blob_client(
            container=app_config.AZURE_STORAGE_OUTPUT_CONTAINER_NAME,
            blob=contents_blob_name,
        )
        contents_blob_client.upload_blob(content.encode("utf-8"), overwrite=True)
        logger.info(
            f"created contents.txt file blob_name={contents_blob_name} (not used for operations)"
        )

        # Step 3: Delete the original blob from input container
        try:
            input_blob_client.delete_blob()
            logger.info(
                f"deleted original blob from input blob_name={original_blob_name}"
            )
        except Exception as e:
            logger.warning(
                f"error deleting blob from input (may already be deleted): {e}"
            )

        db.commit()

    async def _create_segments_and_embeddings(
        self, db: Session, document_id: str, content: str
    ) -> None:
        """Create document segments and generate embeddings.

        Args:
            db: Database session
            document_id: The document ID
            content: The document content
        """
        try:
            logger.info(
                f"starting segment creation and embedding generation for document_id={document_id}"
            )

            # Split text into chunks
            chunks = self.split_markdown_with_headers(text=content)
            logger.info(
                f"split content into {len(chunks)} chunks for document_id={document_id}"
            )

            # Create segments in database with page information
            self._create_document_segments(
                document_id=document_id, chunks=chunks, db=db
            )
            logger.info_structured("created document segments in database", count=len(chunks), document_id=document_id)

            # Generate embeddings for all segments
            await self._generate_embeddings_for_segments(document_id=document_id, db=db)
            logger.info(
                f"generated embeddings for all segments of document_id={document_id}"
            )
        except Exception as e:
            logger.error(
                f"error creating segments and embeddings for document_id={document_id}: {e}"
            )
            raise

    async def _generate_embeddings_for_segments(
        self, db: Session, document_id: str
    ) -> None:
        """Generate embeddings for document segments with rate limiting.

        Args:
            db: Database session
            document_id: The document ID
        """
        segments = (
            db.query(DocumentSegment)
            .filter(
                DocumentSegment.document_id == document_id,
                DocumentSegment.embedding_vector.is_(None),
            )
            .all()
        )

        if not segments:
            return

        texts = [str(segment.content) for segment in segments]

        embeddings_list = await self.embeddings.aembed_documents(texts)

        batch_num = len(embeddings_list) // 20 + 1  # Divide into batches of 20
        for i in range(batch_num):
            start_index = i * 20
            end_index = min((i + 1) * 20, len(embeddings_list))
            batch_segments = segments[start_index:end_index]
            batch_embeddings = embeddings_list[start_index:end_index]

            # Store embeddings for the batch
            for segment, embedding in zip(batch_segments, batch_embeddings):
                segment.embedding_vector = embedding

            db.commit()

            if i < batch_num - 1:
                await asyncio.sleep(1)  # Rate limiting delay between batches

        db.commit()

    @staticmethod
    def split_markdown_with_headers(
        text: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        length_function=len,
        delimiter: str = "<!-- PageBreak -->",
    ) -> list[str]:
        """Split markdown text into chunks using headers and page breaks.

        Args:
            text: The text to split
            chunk_size: Maximum size of each chunk
            chunk_overlap: Overlap between chunks
            length_function: Function to calculate length
            delimiter: Page break delimiter

        Returns:
            List of text chunks
        """
        pages = [p.strip() for p in text.split(delimiter) if p.strip()]

        header_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[("#", "h1"), ("##", "h2"), ("###", "h3")]
        )
        chunker = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=length_function,
        )

        chunks: list[str] = []
        for page in pages:
            # sections is typically a list of Documents with .page_content and .metadata
            sections = header_splitter.split_text(page)
            # If your LangChain version has split_documents, prefer it:
            try:
                chunks.extend(
                    [d.page_content for d in chunker.split_documents(sections)]
                )
            except AttributeError:
                # Fallback: split section contents and drop metadata
                for sec in sections:
                    chunks.extend(chunker.split_text(sec.page_content))
        return chunks

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
        db: Session, document_id: str, raw_blob_name: str
    ) -> None:
        """Update document status to processing.

        Args:
            db: Database session
            document_id: The document ID
            raw_blob_name: The blob name in storage (kept for backwards compatibility, not used for blob operations)
        """
        document = db.query(Document).filter(Document.id == document_id).first()
        if document:
            # Store blob name for reference but don't use it for blob operations
            # Blob paths are constructed from project_id and document_id
            document.original_blob_name = raw_blob_name
            document.status = DocumentStatus.PROCESSING

    @staticmethod
    def _update_document_processed_status(
        db: Session, document_id: str, summary: str
    ) -> None:
        """Update document status to processed.

        Args:
            db: Database session
            document_id: The document ID
            summary: Document summary
        """
        document = db.query(Document).filter(Document.id == document_id).first()
        if document:
            document.status = DocumentStatus.PROCESSED
            document.processed_at = datetime.now()
            document.summary = summary
            db.commit()

    @staticmethod
    def _mark_document_indexed(db: Session, document_id: str) -> None:
        """Mark document as indexed.

        Args:
            db: Database session
            document_id: The document ID
        """
        document = db.query(Document).filter(Document.id == document_id).first()
        if document:
            document.status = DocumentStatus.INDEXED
            db.commit()

    @staticmethod
    def _mark_document_failed(db: Session, document_id: str) -> None:
        """Mark document as failed.

        Args:
            db: Database session
            document_id: The document ID
        """
        document = db.query(Document).filter(Document.id == document_id).first()
        if document:
            document.status = DocumentStatus.FAILED
            db.commit()

    @staticmethod
    def _create_document_segments(
        db: Session,
        document_id: str,
        chunks: list[str],
    ) -> None:
        """Create document segments in database with page information.

        Args:
            db: Database session
            document_id: The document ID
            chunks: List of text chunks
        """
        segments = [
            DocumentSegment(
                document_id=document_id,
                content=chunk,
                content_type="text",
            )
            for chunk in chunks
        ]
        db.add_all(segments)
        db.commit()

    @contextmanager
    def _get_db_session(self):
        """Context manager for database sessions."""
        db = SessionLocal()
        try:
            yield db
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
