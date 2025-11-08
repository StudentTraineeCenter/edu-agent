import asyncio
import uuid
from contextlib import contextmanager
from datetime import datetime
from typing import Optional

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure.storage.blob import BlobServiceClient
from core.config import app_config
from core.logger import get_logger
from core.services.content_understanding import AzureContentUnderstandingClient
from db.enums import DocumentStatus
from db.models import Document, DocumentSegment
from db.session import SessionLocal
from langchain_openai import AzureOpenAIEmbeddings
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)
from sqlalchemy.orm import Session

logger = get_logger(__name__)


class DataProcessingService:
    def __init__(self):
        self.credential = DefaultAzureCredential()

        self.blob_service_client = BlobServiceClient.from_connection_string(
            app_config.AZURE_STORAGE_CONNECTION_STRING
        )

        self.cu_client = AzureContentUnderstandingClient(
            endpoint=app_config.AZURE_CU_ENDPOINT,
            subscription_key=app_config.AZURE_CU_KEY,
        )

        self.token_provider = get_bearer_token_provider(
            self.credential, "https://cognitiveservices.azure.com/.default"
        )

        self.embeddings = AzureOpenAIEmbeddings(
            azure_deployment=app_config.AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
            azure_endpoint=app_config.AZURE_OPENAI_ENDPOINT,
            api_version="2024-12-01-preview",
            azure_ad_token_provider=self.token_provider,
        )

    def upload_document(
        self, file_content: bytes, filename: str, project_id: str, owner_id: str
    ) -> str:
        """Upload document to blob storage and return immediately."""
        with self._get_db_session() as db:
            try:
                logger.info(
                    "uploading document file_name=%s for project_id=%s by owner_id=%s",
                    filename,
                    project_id,
                    owner_id,
                )

                # Step 1: Create document record
                document_id = self._create_document_record(
                    db=db,
                    file_content=file_content,
                    filename=filename,
                    project_id=project_id,
                    owner_id=owner_id,
                )
                logger.info("created document record document_id=%s", document_id)

                # Step 2: Upload to blob storage
                raw_blob_name = self._upload_to_blob_storage(
                    file_content=file_content,
                    filename=filename,
                    project_id=project_id,
                    document_id=document_id,
                )
                logger.info(
                    "uploaded document to blob storage blob_name=%s", raw_blob_name
                )

                # Step 3: Update document with blob reference
                self._update_document_blob_reference(
                    db=db, document_id=document_id, raw_blob_name=raw_blob_name
                )
                logger.info(
                    "updated document with blob reference document_id=%s", document_id
                )

                return document_id

            except Exception as e:
                logger.error("error uploading document: %s", e)
                raise

    async def process_document(
        self, document_id: str, file_content: bytes, project_id: str
    ) -> None:
        """Process document asynchronously: analyze, index, and create embeddings."""
        with self._get_db_session() as db:
            try:
                logger.info("starting document processing document_id=%s", document_id)

                # Step 1: Extract text using Document Intelligence
                analyzed_result = self._analyze_document(file_content=file_content)
                analyzed_content = analyzed_result.get("content", "")
                analyzed_summary = analyzed_result.get("summary", "")

                # Step 2: Store processed text
                processed_blob_name = self._store_processed_text(
                    content=analyzed_content,
                    project_id=project_id,
                    document_id=document_id,
                )
                logger.info("stored processed text blob_name=%s", processed_blob_name)

                # Step 3: Update document status to processed
                self._update_document_processed_status(
                    db=db,
                    document_id=document_id,
                    processed_blob_name=processed_blob_name,
                    summary=analyzed_summary,
                )
                logger.info(
                    "updated document status to processed document_id=%s", document_id
                )

                # Step 4: Create segments and embeddings
                await self._create_segments_and_embeddings(
                    db=db, document_id=document_id, content=analyzed_content
                )
                logger.info(
                    "created segments and embeddings document_id=%s", document_id
                )

                # Step 5: Mark document as indexed
                self._mark_document_indexed(db=db, document_id=document_id)
                logger.info("document successfully indexed document_id=%s", document_id)

            except Exception as e:
                logger.error("error processing document_id=%s: %s", document_id, e)
                self._mark_document_failed(db=db, document_id=document_id)
                raise

    async def process(
        self, file_content: bytes, filename: str, project_id: str, owner_id: str
    ) -> str:
        """Upload document to blob storage and trigger indexing (synchronous version for backward compatibility)."""
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

    @staticmethod
    def _get_file_type(filename: str) -> str:
        """Extract file type from filename."""
        return filename.split(".")[-1].lower() if "." in filename else "unknown"

    def _create_document_record(
        self,
        db: Session,
        file_content: bytes,
        filename: str,
        project_id: str,
        owner_id: str,
    ) -> str:
        """Create initial document record in database."""
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
            "created document record document_id=%s (file_name=%s, size=%d bytes)",
            document.id,
            filename,
            len(file_content),
        )
        return document.id

    def _upload_to_blob_storage(
        self, file_content: bytes, filename: str, project_id: str, document_id: str
    ) -> str:
        """Upload document to blob storage."""
        raw_blob_name = f"raw-documents/{project_id}/{document_id}_{filename}"
        blob_client = self.blob_service_client.get_blob_client(
            container=app_config.AZURE_STORAGE_CONTAINER_NAME, blob=raw_blob_name
        )
        blob_client.upload_blob(data=file_content, overwrite=True)
        logger.info("document uploaded to blob storage blob_name=%s", raw_blob_name)
        return raw_blob_name

    @staticmethod
    def _update_document_blob_reference(
        db: Session, document_id: str, raw_blob_name: str
    ) -> None:
        """Update document with blob storage reference."""
        document = db.query(Document).filter(Document.id == document_id).first()
        if document:
            document.original_blob_name = raw_blob_name
            document.status = DocumentStatus.PROCESSING

    def _analyze_document(self, file_content: bytes) -> dict[str, str]:
        """Analyze document using Azure Content Understanding."""
        response = self.cu_client.begin_analyze_data(
            analyzer_id=app_config.AZURE_CU_ANALYZER_ID, data=file_content
        )
        result = self.cu_client.poll_result(response=response)

        contents_item = result["result"]["contents"][0]

        content = contents_item["markdown"]
        summary = contents_item["fields"]["Summary"]["valueString"]

        return {
            "content": content,
            "summary": summary,
        }

    def _store_processed_text(
        self, content: str, project_id: str, document_id: str
    ) -> str:
        """Store processed text in blob storage."""
        processed_blob_name = f"processed-documents/{project_id}/{document_id}.txt"
        blob_client = self.blob_service_client.get_blob_client(
            container=app_config.AZURE_STORAGE_CONTAINER_NAME,
            blob=processed_blob_name,
        )
        blob_client.upload_blob(content.encode("utf-8"), overwrite=True)
        return processed_blob_name

    @staticmethod
    def _update_document_processed_status(
        db: Session, document_id: str, processed_blob_name: str, summary: str
    ) -> None:
        """Update document status to processed."""
        document: Optional[Document] = (
            db.query(Document).filter(Document.id == document_id).first()
        )
        if document:
            document.processed_text_blob_name = processed_blob_name
            document.status = DocumentStatus.PROCESSED
            document.processed_at = datetime.now()
            document.summary = summary
            db.commit()

    @staticmethod
    def _mark_document_indexed(db: Session, document_id: str) -> None:
        """Mark document as indexed."""
        document: Optional[Document] = (
            db.query(Document).filter(Document.id == document_id).first()
        )
        if document:
            document.status = DocumentStatus.INDEXED
            db.commit()

    @staticmethod
    def _mark_document_failed(db: Session, document_id: str) -> None:
        """Mark document as failed."""
        document: Optional[Document] = (
            db.query(Document).filter(Document.id == document_id).first()
        )
        if document:
            document.status = DocumentStatus.FAILED
            db.commit()

    async def _create_segments_and_embeddings(
        self, db: Session, document_id: str, content: str
    ) -> None:
        """Create document segments and generate embeddings."""
        try:
            logger.info(
                "starting segment creation and embedding generation for document_id=%s",
                document_id,
            )

            # Split text into chunks
            chunks = self.split_markdown_with_headers(text=content)
            logger.info(
                "split content into %d chunks for document_id=%s",
                len(chunks),
                document_id,
            )

            # Create segments in database with page information
            self._create_document_segments(
                document_id=document_id, chunks=chunks, db=db
            )
            logger.info("created %d document segments in database", len(chunks))

            # Generate embeddings for all segments
            await self._generate_embeddings_for_segments(document_id=document_id, db=db)
            logger.info(
                "generated embeddings for all segments of document_id=%s",
                document_id,
            )

        except Exception as e:
            logger.error(
                "error creating segments and embeddings for document_id=%s: %s",
                document_id,
                e,
            )
            raise

    @staticmethod
    def _create_document_segments(
        db: Session,
        document_id: str,
        chunks: list[str],
    ) -> None:
        """Create document segments in database with page information."""
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

    async def _generate_embeddings_for_segments(
        self, db: Session, document_id: str
    ) -> None:
        """Generate embeddings for document segments with rate limiting."""
        segments: list[type[DocumentSegment]] = (
            db.query(DocumentSegment)
            .filter(
                DocumentSegment.document_id == document_id,
                DocumentSegment.embedding_vector.is_(None),
            )
            .all()
        )

        if not segments:
            return

        texts: list[str] = [str(segment.content) for segment in segments]

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
