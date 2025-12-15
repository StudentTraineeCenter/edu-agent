"""Processor for document processing tasks."""

import asyncio
from datetime import datetime
from uuid import uuid4

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure.storage.blob import BlobServiceClient
from langchain_openai import AzureOpenAIEmbeddings
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

from edu_shared.db.models import Document, DocumentSegment
from edu_shared.schemas.documents import DocumentStatus
from edu_shared.schemas.queue import DocumentProcessingData
from edu_shared.services.content_understanding import AzureContentUnderstandingClient
from processors.base import BaseProcessor
from rich.console import Console

console = Console(force_terminal=True)


class DocumentProcessor(BaseProcessor[DocumentProcessingData]):
    """Processor for processing documents with Azure Content Understanding."""

    def __init__(
        self,
        azure_storage_connection_string: str,
        azure_storage_input_container_name: str,
        azure_storage_output_container_name: str,
        azure_cu_endpoint: str,
        azure_cu_key: str,
        azure_cu_analyzer_id: str,
        azure_openai_embedding_deployment: str,
        azure_openai_endpoint: str,
        azure_openai_api_version: str,
    ):
        """Initialize the processor.
        
        Args:
            azure_storage_connection_string: Azure Storage connection string
            azure_storage_input_container_name: Input container name
            azure_storage_output_container_name: Output container name
            azure_cu_endpoint: Azure Content Understanding endpoint
            azure_cu_key: Azure Content Understanding subscription key
            azure_cu_analyzer_id: Azure Content Understanding analyzer ID
            azure_openai_embedding_deployment: Azure OpenAI embedding deployment
            azure_openai_endpoint: Azure OpenAI endpoint
            azure_openai_api_version: Azure OpenAI API version
        """
        self.blob_service_client = BlobServiceClient.from_connection_string(
            azure_storage_connection_string
        )
        self.input_container = azure_storage_input_container_name
        self.output_container = azure_storage_output_container_name

        self.cu_client = AzureContentUnderstandingClient(
            endpoint=azure_cu_endpoint,
            subscription_key=azure_cu_key,
        )

        token_provider = get_bearer_token_provider(
            DefaultAzureCredential(),
            "https://cognitiveservices.azure.com/.default"
        )
        self.embeddings = AzureOpenAIEmbeddings(
            azure_deployment=azure_openai_embedding_deployment,
            azure_endpoint=azure_openai_endpoint,
            api_version=azure_openai_api_version,
            azure_ad_token_provider=token_provider
        )
        self.analyzer_id = azure_cu_analyzer_id

    async def process(self, payload: DocumentProcessingData) -> None:
        """Process document asynchronously: analyze, index, and create embeddings.
        
        Args:
            payload: Document processing data
            
        Raises:
            Exception: If processing fails
        """
        document_id = payload["document_id"]
        project_id = payload["project_id"]

        with self._get_db_session() as db:
            try:
                # Get document to find blob name
                document = db.query(Document).filter(Document.id == document_id).first()
                if not document:
                    raise ValueError(f"Document {document_id} not found")

                # Get blob from input container
                file_extension = (
                    document.file_type if document.file_type != "unknown" else ""
                )
                if file_extension:
                    blob_name = f"{project_id}/{document_id}.{file_extension}"
                else:
                    blob_name = f"{project_id}/{document_id}"

                blob_client = self.blob_service_client.get_blob_client(
                    container=self.input_container, blob=blob_name
                )
                file_content = blob_client.download_blob().readall()

                # Step 1: Extract text using Content Understanding
                analyzed_result = await asyncio.to_thread(
                    self._analyze_document, file_content=file_content
                )
                analyzed_content = analyzed_result["content"]
                analyzed_summary = analyzed_result["summary"]

                # Step 2: Move blob from input to output and create contents.txt
                await asyncio.to_thread(
                    self._move_blob_to_output,
                    content=analyzed_content,
                    project_id=project_id,
                    document_id=document_id,
                    db=db,
                )

                # Step 3: Update document status to processed
                self._update_document_processed_status(
                    db=db,
                    document_id=document_id,
                    summary=analyzed_summary,
                )

                # Step 4: Create segments and embeddings
                await self._create_segments_and_embeddings(
                    db=db, document_id=document_id, content=analyzed_content
                )

                # Step 5: Mark document as indexed
                self._mark_document_indexed(db=db, document_id=document_id)
                
                console.log(f"Processed document {document_id}")
            except Exception:
                self._mark_document_failed(db=db, document_id=document_id)
                raise

    def _analyze_document(self, file_content: bytes) -> dict:
        """Analyze document using Azure Content Understanding.

        Args:
            file_content: The file content as bytes

        Returns:
            Dictionary containing content and summary
        """
        response = self.cu_client.begin_analyze_data(
            analyzer_id=self.analyzer_id, data=file_content
        )
        result = self.cu_client.poll_result(response=response)

        contents_item = result["result"]["contents"][0]

        content = contents_item["markdown"]
        summary = contents_item["fields"]["Summary"]["valueString"]

        return {
            "content": content,
            "summary": summary,
        }

    def _move_blob_to_output(
        self, content: str, project_id: str, document_id: str, db
    ) -> None:
        """Move original blob from input to output and create processed contents file.

        Args:
            content: The processed content
            project_id: The project ID
            document_id: The document ID
            db: Database session
        """
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise ValueError(f"Document {document_id} not found")

        file_extension = document.file_type if document.file_type != "unknown" else ""
        if file_extension:
            original_blob_name = f"{project_id}/{document_id}.{file_extension}"
        else:
            original_blob_name = f"{project_id}/{document_id}"

        contents_blob_name = f"{project_id}/{document_id}.contents.txt"

        # Copy original blob from input to output container
        input_blob_client = self.blob_service_client.get_blob_client(
            container=self.input_container,
            blob=original_blob_name,
        )
        output_blob_client = self.blob_service_client.get_blob_client(
            container=self.output_container,
            blob=original_blob_name,
        )

        blob_data = input_blob_client.download_blob().readall()
        output_blob_client.upload_blob(blob_data, overwrite=True)

        # Create contents.txt file with processed content
        contents_blob_client = self.blob_service_client.get_blob_client(
            container=self.output_container,
            blob=contents_blob_name,
        )
        contents_blob_client.upload_blob(content.encode("utf-8"), overwrite=True)

        # Delete the original blob from input container
        try:
            input_blob_client.delete_blob()
        except Exception:
            pass  # May already be deleted

        db.commit()

    async def _create_segments_and_embeddings(
        self, db, document_id: str, content: str
    ) -> None:
        """Create document segments and generate embeddings.

        Args:
            db: Database session
            document_id: The document ID
            content: The document content
        """
        # Split text into chunks
        chunks = self.split_markdown_with_headers(text=content)

        # Create segments in database
        self._create_document_segments(
            document_id=document_id, chunks=chunks, db=db
        )

        # Generate embeddings for all segments
        await self._generate_embeddings_for_segments(document_id=document_id, db=db)

    async def _generate_embeddings_for_segments(
        self, db, document_id: str
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

        batch_num = len(embeddings_list) // 20 + 1
        for i in range(batch_num):
            start_index = i * 20
            end_index = min((i + 1) * 20, len(embeddings_list))
            batch_segments = segments[start_index:end_index]
            batch_embeddings = embeddings_list[start_index:end_index]

            for segment, embedding in zip(batch_segments, batch_embeddings):
                segment.embedding_vector = embedding

            db.commit()

            if i < batch_num - 1:
                await asyncio.sleep(1)

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
            sections = header_splitter.split_text(page)
            try:
                chunks.extend(
                    [d.page_content for d in chunker.split_documents(sections)]
                )
            except AttributeError:
                for sec in sections:
                    chunks.extend(chunker.split_text(sec.page_content))
        return chunks

    @staticmethod
    def _update_document_processed_status(
        db, document_id: str, summary: str
    ) -> None:
        """Update document status to processed.

        Args:
            db: Database session
            document_id: The document ID
            summary: Document summary
        """
        document = db.query(Document).filter(Document.id == document_id).first()
        if document:
            document.status = DocumentStatus.PROCESSED.value
            document.processed_at = datetime.now()
            document.summary = summary
            db.commit()

    @staticmethod
    def _mark_document_indexed(db, document_id: str) -> None:
        """Mark document as indexed.

        Args:
            db: Database session
            document_id: The document ID
        """
        document = db.query(Document).filter(Document.id == document_id).first()
        if document:
            document.status = DocumentStatus.INDEXED.value
            db.commit()

    @staticmethod
    def _mark_document_failed(db, document_id: str) -> None:
        """Mark document as failed.

        Args:
            db: Database session
            document_id: The document ID
        """
        document = db.query(Document).filter(Document.id == document_id).first()
        if document:
            document.status = DocumentStatus.FAILED.value
            db.commit()

    @staticmethod
    def _create_document_segments(
        db,
        document_id: str,
        chunks: list[str],
    ) -> None:
        """Create document segments in database.

        Args:
            db: Database session
            document_id: The document ID
            chunks: List of text chunks
        """
        segments = [
            DocumentSegment(
                id=str(uuid4()),
                document_id=document_id,
                content=chunk,
                content_type="text",
            )
            for chunk in chunks
        ]
        db.add_all(segments)
        db.commit()
