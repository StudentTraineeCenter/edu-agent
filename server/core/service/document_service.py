from typing import List, Dict, Any, Optional, Tuple
from contextlib import contextmanager

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure.storage.blob import BlobServiceClient
from langchain_openai import AzureOpenAIEmbeddings
from langchain_postgres import PGVectorStore, PGEngine

from core.config import app_config
from core.logger import get_logger
from db.model import Document, Project, ChatMessageSource
from db.session import SessionLocal

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
                if document:
                    logger.info(
                        "found document_id=%s - %s", document_id, document.file_name
                    )
                else:
                    logger.info("document_id=%s not found", document_id)
                return document
            except Exception as e:
                logger.error("error retrieving document_id=%s: %s", document_id, e)
                raise

    async def search_documents(
        self, query: str, project_id: str, top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Search documents using PGVectorStore with proper filtering."""
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

                # Format and return results
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

    @staticmethod
    def _format_search_results(
        similar_docs: List[Tuple[Any, float]],
    ) -> List[Dict[str, Any]]:
        """Format search results for API response."""
        search_results = []
        for doc, score in similar_docs:
            search_results.append(
                {
                    "id": doc.metadata.get("id", ""),
                    "content": doc.page_content,
                    "title": doc.metadata.get("title", ""),
                    "score": 1.0 - float(score),  # Convert distance to similarity score
                }
            )
        return search_results

    async def get_relevant_context(
        self, query: str, project_id: str, top_k: int = 5
    ) -> Tuple[str, list[ChatMessageSource]]:
        """Get relevant context documents for a query using PGVectorStore."""
        with self._get_db_session() as db:
            try:
                logger.info(
                    f"Getting streaming grounded response for project {project_id} with query: '{query[:100]}...' (top_k={top_k})"
                )

                project: Optional[Project] = (
                    db.query(Project).filter(Project.id == project_id).first()
                )
                if not project:
                    logger.info(f"Project {project_id} not found")
                    return "Project not found.", []

                # Get project language code
                language_code = project.language_code
                logger.info(
                    f"Using language code: {language_code} for project {project_id}"
                )

                # Check if project has documents
                documents: list[Document] = project.documents
                doc_ids = [str(doc.id) for doc in documents]
                if not doc_ids:
                    logger.info(f"No documents found for project {project_id}")

                    return "No documents found for this project.", []

                logger.info(f"Found {len(doc_ids)} documents in project {project_id}")

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
                logger.info(f"Retrieved {len(relevant_docs)} relevant documents")

                # Create context from relevant documents with numbered citations
                context_parts = []
                for i, doc in enumerate(relevant_docs, 1):
                    title = doc.metadata.get("title", f"Document {i}")
                    content = doc.page_content[:1000]  # Limit content length
                    context_parts.append(f"[{i}] {title}:\n{content}...")

                context = (
                    "\n\n".join(context_parts)
                    if context_parts
                    else "No relevant documents found."
                )

                sources = []
                for i, relevant_doc in enumerate(relevant_docs, 1):
                    document_id = relevant_doc.metadata.get("document_id", "")
                    # get doc from documents based on id
                    doc = next((d for d in documents if d.id == document_id), None)
                    title = doc.file_name if doc else f"Document {i}"
                    preview_url = f"/v1/documents/{document_id}/preview"

                    sources.append(
                        ChatMessageSource(
                            id=relevant_doc.metadata.get("id", ""),
                            citation_index=i,
                            title=title,
                            document_id=document_id,
                            content=relevant_doc.page_content,
                            preview_url=preview_url,
                            score=relevant_doc.metadata.get("score", 1.0),
                        )
                    )

                return context, sources
            except Exception as e:
                logger.error(
                    f"Error getting streaming grounded response for project {project_id}: {e}"
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
            logger.error(f"Error streaming blob for document {document_id}: {e}")
            raise
