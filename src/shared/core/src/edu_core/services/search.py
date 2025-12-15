"""RAG search service for document retrieval."""

from contextlib import contextmanager
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from langchain_core.documents import Document as LangchainDocument
from langchain_openai import AzureOpenAIEmbeddings
from langchain_postgres import PGEngine, PGVectorStore

from edu_core.db.models import Document, Project
from edu_core.db.session import get_session_factory
from edu_core.exceptions import NotFoundError
from edu_core.schemas.search import SearchResultItem


class SearchService:
    """Service for RAG-based document search using LangChain PGVectorStore."""

    def __init__(
        self,
        database_url: str,
        azure_openai_embedding_deployment: str,
        azure_openai_endpoint: str,
        azure_openai_api_version: str,
    ) -> None:
        """Initialize the search service.

        Args:
            database_url: PostgreSQL database connection URL
            embeddings: LangChain embeddings service for vector operations
        """
        self.database_url = database_url

        token_provider = get_bearer_token_provider(
            DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
        )
        self.embeddings = AzureOpenAIEmbeddings(
            azure_deployment=azure_openai_embedding_deployment,
            azure_endpoint=azure_openai_endpoint,
            api_version=azure_openai_api_version,
            azure_ad_token_provider=token_provider,
        )
        self._vector_store: PGVectorStore | None = None

    async def search_documents(
        self,
        query: str,
        project_id: str,
        top_k: int = 5,
    ) -> list[SearchResultItem]:
        """Search documents using vector similarity search.

        Args:
            query: The search query
            project_id: The project ID to search within
            top_k: Number of results to return

        Returns:
            List of SearchResultItem instances

        Raises:
            NotFoundError: If project not found
        """
        with self._get_db_session() as db:
            try:
                # Get project and validate it exists
                project = db.query(Project).filter(Project.id == project_id).first()
                if not project:
                    raise NotFoundError(f"Project {project_id} not found")

                # Get document IDs for the project
                document_ids = [str(doc.id) for doc in project.documents]
                if not document_ids:
                    return []

                # Get or create vector store
                vector_store = await self._get_vector_store()

                # Perform vector search
                similar_docs = await vector_store.asimilarity_search_with_score(
                    query, k=top_k, filter={"document_id": {"$in": document_ids}}
                )

                # Format and return typed results
                return self._format_search_results(similar_docs, db)
            except NotFoundError:
                raise
            except Exception:
                raise

    async def _get_vector_store(self) -> PGVectorStore:
        """Get or create PGVectorStore instance.

        Returns:
            PGVectorStore instance
        """
        if self._vector_store is not None:
            return self._vector_store

        # Convert psycopg2 URL to asyncpg URL
        async_url = self.database_url.replace(
            "postgresql+psycopg2://", "postgresql+asyncpg://"
        )

        # Remove unsupported query parameters - asyncpg handles SSL differently
        parsed = urlparse(async_url)
        query_params = parse_qs(parsed.query)

        # Remove parameters that asyncpg doesn't support
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

        self._vector_store = await PGVectorStore.create(
            pg_engine,
            table_name="document_segments",
            embedding_service=self.embeddings,
            id_column="id",
            content_column="content",
            embedding_column="embedding_vector",
            metadata_columns=["id", "document_id"],
        )

        return self._vector_store

    def _format_search_results(
        self,
        similar_docs: list[tuple[LangchainDocument, float]],
        db,
    ) -> list[SearchResultItem]:
        """Format search results with validated typed models.

        Args:
            similar_docs: List of tuples containing (document, score)
            db: Database session for querying document metadata

        Returns:
            List of SearchResultItem instances
        """
        if not similar_docs:
            return []

        # Group by document_id and get document metadata
        from collections import defaultdict

        grouped = defaultdict(list)
        for doc, score in similar_docs:
            doc_id = doc.metadata.get("document_id", "")
            if doc_id:
                grouped[doc_id].append((doc, score))

        # Get all document metadata in one query
        doc_ids = list(grouped.keys())
        documents = db.query(Document).filter(Document.id.in_(doc_ids)).all()
        doc_map = {str(d.id): d for d in documents}

        results = []
        for i, (doc_id, chunks) in enumerate(grouped.items(), start=1):
            # Combine top segments
            top_chunks = sorted(chunks, key=lambda x: x[1])[:3]
            combined_text = "\n".join(
                c[0].page_content[:500] for c in top_chunks if c[0].page_content
            )

            if not combined_text.strip():
                continue

            doc_meta = doc_map.get(str(doc_id))

            # Get segment ID from first chunk
            segment_id = top_chunks[0][0].metadata.get("id", doc_id)

            try:
                # Get the best score from top chunks
                best_score = min([c[1] for c in top_chunks]) if top_chunks else 1.0
                # Normalize score (lower is better in similarity search, so invert)
                normalized_score = max(0.0, min(1.0, 1.0 - best_score))

                result = SearchResultItem(
                    id=segment_id,
                    document_id=doc_id,
                    title=doc_meta.file_name if doc_meta else "Unknown Document",
                    content=combined_text,
                    score=normalized_score,
                )
                results.append(result)
            except Exception:
                # Skip invalid results
                continue

        return results

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
