from collections import defaultdict
from contextlib import contextmanager
from typing import List, Optional, Tuple

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure.storage.blob import BlobServiceClient
from core.config import app_config
from core.logger import get_logger
from core.services.document_types import (
    ContextSource,
    DocumentMetadata,
    SearchResultItem,
)
from db.models import ChatMessageSource, Document, Project
from db.session import SessionLocal
from langchain_core.documents import Document as LangchainDocument
from langchain_openai import AzureOpenAIEmbeddings
from langchain_postgres import PGEngine, PGVectorStore
from pydantic import ValidationError

logger = get_logger(__name__)


class DocumentService:
    """Production-ready document service for handling document upload, processing, and search."""

    def __init__(self):
        """Initialize the document service with Azure clients and LangChain components."""
        self.credential = DefaultAzureCredential()

        self.blob_service_client = BlobServiceClient.from_connection_string(
            app_config.AZURE_STORAGE_CONNECTION_STRING
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

    def list_documents(self, project_id: str, user_id: str) -> List[Document]:
        """List all documents for a project."""
        with self._get_db_session() as db:
            try:
                logger.info("listing documents for project_id=%s", project_id)
                documents = (
                    db.query(Document)
                    .filter(
                        Document.project_id == project_id, Document.owner_id == user_id
                    )
                    .order_by(Document.uploaded_at.desc())
                    .all()
                )
                logger.info(
                    "found %d documents for project_id=%s", len(documents), project_id
                )
                return documents
            except Exception as e:
                logger.error(
                    "error listing documents for project_id=%s: %s", project_id, e
                )
                raise

    def get_document(self, document_id: str, user_id: str) -> Optional[Document]:
        """Get a document by ID."""
        with self._get_db_session() as db:
            try:
                logger.info("retrieving document_id=%s", document_id)
                document = (
                    db.query(Document)
                    .filter(Document.id == document_id, Document.owner_id == user_id)
                    .first()
                )
                if not document:
                    logger.info("document_id=%s not found", document_id)
                    raise ValueError(f"Document with id {document_id} not found")

                return document
            except Exception as e:
                logger.error("error retrieving document_id=%s: %s", document_id, e)
                raise

    async def search_documents(
        self, query: str, project_id: str, top_k: int = 5
    ) -> List[SearchResultItem]:
        """Search documents using PGVectorStore with proper filtering and typed results."""
        with self._get_db_session() as db:
            try:
                logger.info(
                    "searching documents for project_id=%s with query: '%.100s...' (top_k=%d)",
                    project_id,
                    query,
                    top_k,
                )

                project: Optional[Project] = (
                    db.query(Project).filter(Project.id == project_id).first()
                )
                if not project:
                    logger.info("project_id=%s not found", project_id)
                    raise ValueError(f"Project {project_id} not found")

                # Get document IDs for the project
                document_ids = [str(doc.id) for doc in project.documents]
                if not document_ids:
                    logger.info("no documents found for project_id=%s", project_id)
                    return []

                logger.info(
                    "found %d documents for project_id=%s",
                    len(document_ids),
                    project_id,
                )

                # Create vector store and perform search
                vectorstore = await self._create_vector_store()
                similar_docs = await vectorstore.asimilarity_search_with_score(
                    query, k=top_k, filter={"document_id": {"$in": document_ids}}
                )

                # Format and return typed results
                results = self._format_search_results(similar_docs)
                logger.info(
                    "found %d documents for project_id=%s", len(results), project_id
                )
                return results

            except Exception as e:
                logger.error(
                    "error searching documents for project_id=%s: %s", project_id, e
                )
                raise

    async def _create_vector_store(self) -> PGVectorStore:
        """Create PGVectorStore instance."""
        async_url = app_config.DATABASE_URL.replace(
            "postgresql+psycopg2://", "postgresql+asyncpg://"
        )
        pg_engine = PGEngine.from_connection_string(url=async_url)

        return await PGVectorStore.create(
            pg_engine,
            table_name="document_segments",
            embedding_service=self.embeddings,
            id_column="id",
            content_column="content",
            embedding_column="embedding_vector",
            metadata_columns=["id", "document_id"],
        )

    def _format_search_results(
        self,
        similar_docs: List[Tuple[LangchainDocument, float]],
    ) -> List[SearchResultItem]:
        """Format search results with validated typed models."""
        with self._get_db_session() as db:

            def _group_segments_by_document(similar_docs):
                grouped = defaultdict(list)
                for doc, score in similar_docs:
                    # Validate metadata structure
                    try:
                        metadata = DocumentMetadata(
                            segment_id=doc.metadata.get("id", ""),
                            document_id=doc.metadata.get("document_id", ""),
                            title=doc.metadata.get("title"),
                            score=1.0 - float(score) if score else None,
                        )
                        grouped[metadata.document_id].append((doc, score, metadata))
                    except ValidationError as e:
                        logger.warning(
                            "Invalid metadata for document segment, skipping: %s", e
                        )
                        continue
                return grouped

            grouped = _group_segments_by_document(similar_docs)

            doc_ids = list(grouped.keys())
            documents = db.query(Document).filter(Document.id.in_(doc_ids)).all()
            doc_map = {str(d.id): d for d in documents}

            results = []
            for i, (doc_id, chunks) in enumerate(grouped.items(), start=1):
                # Combine top segments (shorten to avoid context overflow)
                top_chunks = sorted(chunks, key=lambda x: x[1])[:3]
                combined_text = "\n".join(
                    c[0].page_content[:500] for c in top_chunks if c[0].page_content
                )

                if not combined_text.strip():
                    logger.warning("Empty content for document %s, skipping", doc_id)
                    continue

                doc_meta = doc_map.get(str(doc_id))
                avg_score = 1.0 - float(sum(c[1] for c in top_chunks) / len(top_chunks))

                try:
                    result = SearchResultItem(
                        citation_index=i,
                        document_id=doc_id,
                        title=doc_meta.file_name if doc_meta else "Unknown Document",
                        content=combined_text,
                        score=avg_score,
                    )
                    results.append(result)
                except ValidationError as e:
                    logger.error("Failed to create search result item: %s", e)
                    continue

            return results

    async def get_relevant_context(
        self, query: str, project_id: str, top_k: int = 5
    ) -> Tuple[str, list[ChatMessageSource]]:
        """Get relevant context documents for a query using PGVectorStore with typed validation."""
        with self._get_db_session() as db:
            try:
                logger.info(
                    "getting streaming grounded response for project_id=%s with query: '%.100s...' (top_k=%d)",
                    project_id,
                    query,
                    top_k,
                )

                project: Optional[Project] = (
                    db.query(Project).filter(Project.id == project_id).first()
                )
                if not project:
                    logger.info("project_id=%s not found", project_id)
                    return "Project not found.", []

                # Get project language code
                language_code = project.language_code
                logger.info(
                    "using language_code=%s for project_id=%s",
                    language_code,
                    project_id,
                )

                # Check if project has documents
                documents: list[Document] = project.documents
                doc_ids = [str(doc.id) for doc in documents]
                if not doc_ids:
                    logger.info("no documents found for project_id=%s", project_id)
                    return "No documents found for this project.", []

                logger.info(
                    "found %d documents in project_id=%s", len(doc_ids), project_id
                )

                # Set up vector store and get relevant documents first
                vectorstore = await self._create_vector_store()
                retriever = vectorstore.as_retriever(
                    search_kwargs={
                        "k": top_k,
                        "filter": {"document_id": {"$in": doc_ids}},
                    }
                )

                # Get relevant documents for context
                relevant_docs = await retriever.ainvoke(query)
                logger.info("retrieved %d relevant documents", len(relevant_docs))

                # Create context from relevant documents with numbered citations
                context_parts = []
                sources = []
                citation_idx = 1

                for doc in relevant_docs:
                    try:
                        # Validate metadata - segment ID is stored as "id" in vector store
                        metadata = DocumentMetadata(
                            segment_id=doc.metadata.get("id", ""),
                            document_id=doc.metadata.get("document_id", ""),
                            title=doc.metadata.get("title"),
                            score=doc.metadata.get("score", 1.0),
                        )

                        # Find the actual document
                        actual_doc = next(
                            (d for d in documents if str(d.id) == metadata.document_id),
                            None,
                        )
                        title = (
                            actual_doc.file_name
                            if actual_doc
                            else f"Document {citation_idx}"
                        )
                        content = doc.page_content[:1000] if doc.page_content else ""

                        if not content.strip():
                            logger.warning("Empty content for segment, skipping")
                            continue

                        context_parts.append(f"[{citation_idx}] {title}:\n{content}...")

                        # Create validated source with segment ID
                        source = ContextSource(
                            id=metadata.segment_id,
                            citation_index=citation_idx,
                            title=title,
                            document_id=metadata.document_id,
                            content=doc.page_content or "",
                            preview_url=f"/v1/documents/{metadata.document_id}/preview",
                            score=metadata.score or 1.0,
                        )

                        # Convert to ChatMessageSource for backwards compatibility
                        sources.append(
                            ChatMessageSource(
                                id=source.id,
                                citation_index=source.citation_index,
                                title=source.title,
                                document_id=source.document_id,
                                content=source.content,
                                preview_url=source.preview_url,
                                score=source.score,
                            )
                        )
                        citation_idx += 1

                    except ValidationError as e:
                        logger.warning("Invalid document metadata, skipping: %s", e)
                        continue

                context = (
                    "\n\n".join(context_parts)
                    if context_parts
                    else "No relevant documents found."
                )

                return context, sources
            except Exception as e:
                logger.error(
                    "error getting streaming grounded response for project_id=%s: %s",
                    project_id,
                    e,
                )
                raise e

    def get_document_blob_stream(self, document_id: str, user_id: str):
        """Get blob content as a streaming iterator for a document."""
        try:
            with self._get_db_session() as db:
                document = (
                    db.query(Document)
                    .filter(Document.id == document_id, Document.owner_id == user_id)
                    .first()
                )
                if not document or not document.original_blob_name:
                    raise ValueError(f"Document {document_id} not found or has no blob")

                blob_client = self.blob_service_client.get_blob_client(
                    container=app_config.AZURE_STORAGE_CONTAINER_NAME,
                    blob=document.original_blob_name,
                )

                # Download blob as a stream
                download_stream = blob_client.download_blob()

                # Return chunks for streaming
                def iterfile():
                    for chunk in download_stream.chunks():
                        yield chunk

                return iterfile()

        except Exception as e:
            logger.error("error streaming blob for document_id=%s: %s", document_id, e)
            raise

    def delete_document(self, document_id: str, user_id: str) -> bool:
        """Delete a document and all its associated blobs."""
        with self._get_db_session() as db:
            try:
                logger.info("deleting document_id=%s", document_id)
                document = (
                    db.query(Document)
                    .filter(Document.id == document_id, Document.owner_id == user_id)
                    .first()
                )
                if not document:
                    logger.info("document_id=%s not found", document_id)
                    raise ValueError(f"Document with id {document_id} not found")

                # Delete original blob from Azure Storage if it exists
                if document.original_blob_name:
                    try:
                        blob_client = self.blob_service_client.get_blob_client(
                            container=app_config.AZURE_STORAGE_CONTAINER_NAME,
                            blob=document.original_blob_name,
                        )
                        blob_client.delete_blob()
                        logger.info(
                            "deleted original blob blob_name=%s for document_id=%s",
                            document.original_blob_name,
                            document_id,
                        )
                    except Exception as e:
                        logger.warning(
                            "error deleting original blob blob_name=%s for document_id=%s: %s",
                            document.original_blob_name,
                            document_id,
                            e,
                        )

                # Delete processed text blob from Azure Storage if it exists
                if document.processed_text_blob_name:
                    try:
                        processed_blob_client = self.blob_service_client.get_blob_client(
                            container=app_config.AZURE_STORAGE_CONTAINER_NAME,
                            blob=document.processed_text_blob_name,
                        )
                        processed_blob_client.delete_blob()
                        logger.info(
                            "deleted processed text blob blob_name=%s for document_id=%s",
                            document.processed_text_blob_name,
                            document_id,
                        )
                    except Exception as e:
                        logger.warning(
                            "error deleting processed text blob blob_name=%s for document_id=%s: %s",
                            document.processed_text_blob_name,
                            document_id,
                            e,
                        )

                # Delete document from database (cascade will delete segments)
                db.delete(document)
                db.commit()

                logger.info("deleted document_id=%s", document_id)
                return True

            except ValueError:
                raise
            except Exception as e:
                logger.error("error deleting document_id=%s: %s", document_id, e)
                db.rollback()
                raise
