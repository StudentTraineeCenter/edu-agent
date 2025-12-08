"""Service for handling document upload, processing, and search."""

from collections import defaultdict
from contextlib import contextmanager
from typing import List, Optional, Tuple
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta
from langchain_core.documents import Document as LangchainDocument
from langchain_openai import AzureOpenAIEmbeddings
from langchain_postgres import PGEngine, PGVectorStore
from pydantic import ValidationError

from core.config import app_config
from core.logger import get_logger
from schemas.documents import (
    ContextSource,
    DocumentMetadata,
    SearchResultItem,
)
from db.enums import DocumentStatus
from db.models import ChatMessageSource, Document, Project
from db.session import SessionLocal

logger = get_logger(__name__)


class DocumentService:
    """Service for handling document upload, processing, and search."""

    def __init__(self) -> None:
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

    def list_documents(self, project_id: str, user_id: str) -> List[Document]:
        """List all documents for a project.

        Args:
            project_id: The project ID
            user_id: The user's ID

        Returns:
            List of Document model instances
        """
        with self._get_db_session() as db:
            try:
                logger.info_structured("listing documents", project_id=project_id)
                documents = (
                    db.query(Document)
                    .filter(
                        Document.project_id == project_id, Document.owner_id == user_id
                    )
                    .order_by(Document.uploaded_at.desc())
                    .all()
                )
                logger.info(
                    f"found {len(documents)} documents for project_id={project_id}"
                )
                return documents
            except Exception as e:
                logger.error(
                    f"error listing documents for project_id={project_id}: {e}"
                )
                raise

    def get_document(self, document_id: str, user_id: str) -> Document:
        """Get a document by ID.

        Args:
            document_id: The document ID
            user_id: The user's ID

        Returns:
            Document model instance

        Raises:
            ValueError: If document not found
        """
        with self._get_db_session() as db:
            try:
                logger.info_structured("retrieving document", document_id=document_id)
                document = (
                    db.query(Document)
                    .filter(Document.id == document_id, Document.owner_id == user_id)
                    .first()
                )
                if not document:
                    raise ValueError(f"Document {document_id} not found")

                logger.info_structured("retrieved document", document_id=document_id)
                return document
            except ValueError:
                raise
            except Exception as e:
                logger.error_structured("error retrieving document", document_id=document_id, error=str(e), exc_info=True)
                raise

    async def search_documents(
        self, query: str, project_id: str, top_k: int = 5
    ) -> List[SearchResultItem]:
        """Search documents using PGVectorStore with proper filtering and typed results.

        Args:
            query: The search query
            project_id: The project ID
            top_k: Number of results to return

        Returns:
            List of SearchResultItem instances
        """
        with self._get_db_session() as db:
            try:
                logger.info(
                    f"searching documents for project_id={project_id} with query: '{query[:100]}...' (top_k={top_k})"
                )

                project = db.query(Project).filter(Project.id == project_id).first()
                if not project:
                    raise ValueError(f"Project {project_id} not found")

                # Get document IDs for the project
                document_ids = [str(doc.id) for doc in project.documents]
                if not document_ids:
                    logger.info_structured("no documents found", project_id=project_id)
                    return []

                logger.info(
                    f"found {len(document_ids)} documents for project_id={project_id}"
                )

                # Create vector store and perform search
                vectorstore = await self._create_vector_store()
                similar_docs = await vectorstore.asimilarity_search_with_score(
                    query, k=top_k, filter={"document_id": {"$in": document_ids}}
                )

                # Format and return typed results
                results = self._format_search_results(similar_docs)
                logger.info(
                    f"found {len(results)} documents for project_id={project_id}"
                )
                return results
            except ValueError:
                raise
            except Exception as e:
                logger.error(
                    f"error searching documents for project_id={project_id}: {e}"
                )
                raise

    async def get_relevant_context(
        self, query: str, project_id: str, top_k: int = 5
    ) -> Tuple[str, list[ChatMessageSource]]:
        """Get relevant context documents for a query using PGVectorStore with typed validation.

        Args:
            query: The search query
            project_id: The project ID
            top_k: Number of results to return

        Returns:
            Tuple of (context string, list of ChatMessageSource)
        """
        with self._get_db_session() as db:
            try:
                logger.info(
                    f"getting streaming grounded response for project_id={project_id} with query: '{query[:100]}...' (top_k={top_k})"
                )

                project = db.query(Project).filter(Project.id == project_id).first()
                if not project:
                    logger.info_structured("project not found", project_id=project_id)
                    return "Project not found.", []

                # Get project language code
                language_code = project.language_code
                logger.info(
                    f"using language_code={language_code} for project_id={project_id}"
                )

                # Check if project has documents
                documents = project.documents
                doc_ids = [str(doc.id) for doc in documents]
                if not doc_ids:
                    logger.info_structured("no documents found", project_id=project_id)
                    return "No documents found for this project.", []

                logger.info(
                    f"found {len(doc_ids)} documents in project_id={project_id}"
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
                logger.info_structured("retrieved relevant documents", count=len(relevant_docs), project_id=project_id)

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
                            logger.warning_structured("empty content for segment, skipping", document_id=document_id)
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
                        logger.warning_structured("invalid document metadata, skipping", error=str(e))
                        continue

                context = (
                    "\n\n".join(context_parts)
                    if context_parts
                    else "No relevant documents found."
                )

                return context, sources
            except Exception as e:
                logger.error(
                    f"error getting streaming grounded response for project_id={project_id}: {e}"
                )
                raise

    def get_document_blob_sas_url(
        self, document_id: str, user_id: str, expiry_minutes: int = 60
    ) -> str:
        """Get a SAS URL for direct blob access.

        Args:
            document_id: The document ID
            user_id: The user's ID
            expiry_minutes: Minutes until the SAS token expires (default: 60)

        Returns:
            Full URL with SAS token for direct blob access

        Raises:
            ValueError: If document not found or has no blob
        """
        try:
            with self._get_db_session() as db:
                document = (
                    db.query(Document)
                    .filter(Document.id == document_id, Document.owner_id == user_id)
                    .first()
                )

                if not document:
                    raise ValueError(f"Document {document_id} not found")

                # Construct blob paths from project_id and document_id
                file_extension = (
                    document.file_type if document.file_type != "unknown" else ""
                )
                if file_extension:
                    blob_name = f"{document.project_id}/{document_id}.{file_extension}"
                else:
                    blob_name = f"{document.project_id}/{document_id}"

                # Determine container: output if processed, input if not yet processed
                if (
                    document.status == DocumentStatus.PROCESSED
                    or document.status == DocumentStatus.INDEXED
                ):
                    # Processed: original file is in output container
                    container_name = app_config.AZURE_STORAGE_OUTPUT_CONTAINER_NAME
                else:
                    # Not yet processed: original file is in input container
                    container_name = app_config.AZURE_STORAGE_INPUT_CONTAINER_NAME

                # Parse connection string to get account name and key
                conn_str = app_config.AZURE_STORAGE_CONNECTION_STRING
                account_name = None
                account_key = None
                for part in conn_str.split(";"):
                    if part.startswith("AccountName="):
                        account_name = part.split("=", 1)[1]
                    elif part.startswith("AccountKey="):
                        account_key = part.split("=", 1)[1]

                if not account_name or not account_key:
                    raise ValueError(
                        "Could not parse storage account name/key from connection string"
                    )

                # Generate SAS token
                sas_token = generate_blob_sas(
                    account_name=account_name,
                    container_name=container_name,
                    blob_name=blob_name,
                    account_key=account_key,
                    permission=BlobSasPermissions(read=True),
                    expiry=datetime.now() + timedelta(minutes=expiry_minutes),
                )

                # Get blob URL
                blob_client = self.blob_service_client.get_blob_client(
                    container=container_name,
                    blob=blob_name,
                )

                return f"{blob_client.url}?{sas_token}"
        except ValueError:
            raise
        except Exception as e:
            logger.error_structured("error generating SAS URL", document_id=document_id, error=str(e), exc_info=True)
            raise

    def get_document_blob_stream(self, document_id: str, user_id: str):
        """Get blob content as a streaming iterator for a document.

        Args:
            document_id: The document ID
            user_id: The user's ID

        Returns:
            Iterator yielding blob chunks

        Raises:
            ValueError: If document not found or has no blob
        """
        try:
            with self._get_db_session() as db:
                document = (
                    db.query(Document)
                    .filter(Document.id == document_id, Document.owner_id == user_id)
                    .first()
                )
                if not document:
                    raise ValueError(f"Document {document_id} not found")

                # Construct blob paths from project_id and document_id
                file_extension = (
                    document.file_type if document.file_type != "unknown" else ""
                )
                if file_extension:
                    blob_name = f"{document.project_id}/{document_id}.{file_extension}"
                else:
                    blob_name = f"{document.project_id}/{document_id}"

                # Determine container: output if processed, input if not yet processed
                if (
                    document.status == DocumentStatus.PROCESSED
                    or document.status == DocumentStatus.INDEXED
                ):
                    # Processed: original file is in output container
                    container_name = app_config.AZURE_STORAGE_OUTPUT_CONTAINER_NAME
                else:
                    # Not yet processed: original file is in input container
                    container_name = app_config.AZURE_STORAGE_INPUT_CONTAINER_NAME

                blob_client = self.blob_service_client.get_blob_client(
                    container=container_name,
                    blob=blob_name,
                )

                # Download blob as a stream
                download_stream = blob_client.download_blob()

                # Return chunks for streaming
                def iterfile():
                    for chunk in download_stream.chunks():
                        yield chunk

                return iterfile()
        except ValueError:
            raise
        except Exception as e:
            logger.error_structured("error streaming blob", document_id=document_id, error=str(e), exc_info=True)
            raise

    def delete_document(self, document_id: str, user_id: str) -> bool:
        """Delete a document and all its associated blobs.

        Args:
            document_id: The document ID
            user_id: The user's ID

        Returns:
            True if deleted successfully

        Raises:
            ValueError: If document not found
        """
        with self._get_db_session() as db:
            try:
                logger.info_structured("deleting document", document_id=document_id)
                document = (
                    db.query(Document)
                    .filter(Document.id == document_id, Document.owner_id == user_id)
                    .first()
                )
                if not document:
                    raise ValueError(f"Document {document_id} not found")

                # Construct blob paths from project_id and document_id
                file_extension = (
                    document.file_type if document.file_type != "unknown" else ""
                )
                if file_extension:
                    original_blob_name = (
                        f"{document.project_id}/{document_id}.{file_extension}"
                    )
                else:
                    original_blob_name = f"{document.project_id}/{document_id}"

                # Delete original blob - check both containers (input if not processed, output if processed)
                # Try input container first (if not yet processed)
                try:
                    input_blob_client = self.blob_service_client.get_blob_client(
                        container=app_config.AZURE_STORAGE_INPUT_CONTAINER_NAME,
                        blob=original_blob_name,
                    )
                    input_blob_client.delete_blob()
                    logger.info(
                        f"deleted original blob from input blob_name={original_blob_name} for document_id={document_id}"
                    )
                except Exception as e:
                    # If not in input, try output container (already processed)
                    try:
                        output_blob_client = self.blob_service_client.get_blob_client(
                            container=app_config.AZURE_STORAGE_OUTPUT_CONTAINER_NAME,
                            blob=original_blob_name,
                        )
                        output_blob_client.delete_blob()
                        logger.info(
                            f"deleted original blob from output blob_name={original_blob_name} for document_id={document_id}"
                        )
                    except Exception as e2:
                        logger.warning(
                            f"error deleting original blob blob_name={original_blob_name} for document_id={document_id}: {e2}"
                        )

                # Delete contents.txt blob from output container if document was processed
                if (
                    document.status == DocumentStatus.PROCESSED
                    or document.status == DocumentStatus.INDEXED
                ):
                    try:
                        contents_blob_name = (
                            f"{document.project_id}/{document_id}.contents.txt"
                        )
                        contents_blob_client = self.blob_service_client.get_blob_client(
                            container=app_config.AZURE_STORAGE_OUTPUT_CONTAINER_NAME,
                            blob=contents_blob_name,
                        )
                        contents_blob_client.delete_blob()
                        logger.info(
                            f"deleted contents.txt blob blob_name={contents_blob_name} for document_id={document_id}"
                        )
                    except Exception as e:
                        logger.warning(
                            f"error deleting contents.txt blob for document_id={document_id}: {e}"
                        )

                # Delete document from database (cascade will delete segments)
                db.delete(document)
                db.commit()

                logger.info_structured("deleted document", document_id=document_id)
                return True
            except ValueError:
                raise
            except Exception as e:
                logger.error_structured("error deleting document", document_id=document_id, error=str(e), exc_info=True)
                raise

    async def _create_vector_store(self) -> PGVectorStore:
        """Create PGVectorStore instance.

        Returns:
            PGVectorStore instance
        """
        # Convert psycopg2 URL to asyncpg URL
        async_url = app_config.DATABASE_URL.replace(
            "postgresql+psycopg2://", "postgresql+asyncpg://"
        )

        # Remove unsupported query parameters - asyncpg handles SSL differently
        # Parse URL to remove query parameters that asyncpg doesn't support
        parsed = urlparse(async_url)
        query_params = parse_qs(parsed.query)

        # Remove parameters that asyncpg doesn't support
        # asyncpg will use SSL by default for secure connections
        query_params.pop("sslmode", None)
        query_params.pop("channel_binding", None)

        # Rebuild URL without unsupported parameters
        new_query = urlencode(query_params, doseq=True)
        async_url = urlunparse(
            (
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                new_query,
                parsed.fragment,
            )
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
        """Format search results with validated typed models.

        Args:
            similar_docs: List of tuples containing documents and scores

        Returns:
            List of SearchResultItem instances
        """
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
                            f"invalid metadata for document segment, skipping: {e}"
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
                    logger.warning_structured("empty content for document, skipping", doc_id=doc_id)
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
                    logger.error_structured("failed to create search result item", doc_id=doc_id, error=str(e), exc_info=True)
                    continue

            return results

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
