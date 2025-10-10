import uuid
import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple, AsyncGenerator
from datetime import datetime
from contextlib import contextmanager

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from azure.storage.blob import BlobServiceClient
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import AzureOpenAIEmbeddings, AzureChatOpenAI
from langchain_postgres import PGVectorStore, PGEngine
from langchain.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate
from sqlalchemy.orm import Session

from core.config import app_config
from core.logger import get_logger
from db.model import Document, DocumentSegment, Project
from db.session import SessionLocal

logger = get_logger(__name__)


class DocumentService:
    """Production-ready document service for handling document upload, processing, and search."""

    def __init__(self):
        """Initialize the document service with Azure clients and LangChain components."""
        self._setup_azure_clients()
        self._setup_langchain_components()

    def _setup_azure_clients(self) -> None:
        """Initialize Azure service clients."""
        self.credential = DefaultAzureCredential()

        self.doc_intel_client = DocumentIntelligenceClient(
            endpoint=app_config.AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT,
            credential=AzureKeyCredential(app_config.AZURE_DOCUMENT_INTELLIGENCE_KEY),
        )

        self.blob_service_client = BlobServiceClient.from_connection_string(
            app_config.AZURE_STORAGE_CONNECTION_STRING
        )

        self.token_provider = get_bearer_token_provider(
            self.credential, "https://cognitiveservices.azure.com/.default"
        )

    def _setup_langchain_components(self) -> None:
        """Initialize LangChain components for text processing and embeddings."""
        self.embeddings = AzureOpenAIEmbeddings(
            azure_deployment=app_config.AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
            azure_endpoint=app_config.AZURE_OPENAI_ENDPOINT,
            api_version="2024-12-01-preview",
            azure_ad_token_provider=self.token_provider,
        )

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
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

    async def upload_document(
        self, file_content: bytes, filename: str, project_id: str, owner_id: str
    ) -> str:
        """Upload document to blob storage and trigger indexing."""
        document_id = None
        try:
            logger.info(
                f"Starting document upload: {filename} for project {project_id} by user {owner_id}"
            )

            # Step 1: Create document record
            document_id = self._create_document_record(
                file_content, filename, project_id, owner_id
            )
            logger.info(f"Created document record: {document_id}")

            # Step 2: Upload to blob storage
            raw_blob_name = self._upload_to_blob_storage(
                file_content, filename, project_id, document_id
            )
            logger.info(f"Uploaded document to blob storage: {raw_blob_name}")

            # Step 3: Update document with blob reference
            self._update_document_blob_reference(document_id, raw_blob_name)
            logger.info(f"Updated document with blob reference: {document_id}")

            # Step 4: Extract text using Document Intelligence
            content, char_to_page = self._extract_text_from_document(file_content)
            logger.info(
                f"Extracted text from document: {len(content)} characters with page mapping"
            )

            # Step 5: Store processed text
            processed_blob_name = self._store_processed_text(
                content, project_id, document_id
            )
            logger.info(f"Stored processed text: {processed_blob_name}")

            # Step 6: Update document status to processed
            self._update_document_processed_status(document_id, processed_blob_name)
            logger.info(f"Updated document status to processed: {document_id}")

            # Step 7: Create segments and embeddings
            await self._create_segments_and_embeddings(
                document_id, content, char_to_page
            )
            logger.info(f"Created segments and embeddings: {document_id}")

            # Step 8: Mark document as indexed
            self._mark_document_indexed(document_id)
            logger.info(f"Document successfully indexed: {document_id}")
            return document_id

        except Exception as e:
            logger.error(f"Error processing document {document_id}: {e}")
            if document_id:
                self._mark_document_failed(document_id)
            raise

    def _create_document_record(
        self, file_content: bytes, filename: str, project_id: str, owner_id: str
    ) -> str:
        """Create initial document record in database."""
        with self._get_db_session() as db:
            document = Document(
                id=str(uuid.uuid4()),
                owner_id=owner_id,
                project_id=project_id,
                file_name=filename,
                file_type=self._get_file_type(filename),
                file_size=len(file_content),
                status="uploaded",
                uploaded_at=datetime.now(),
            )
            db.add(document)
            db.commit()
            db.refresh(document)
            logger.info(
                f"Created document record: {document.id} ({filename}, {len(file_content)} bytes)"
            )
            return document.id

    def _get_file_type(self, filename: str) -> str:
        """Extract file type from filename."""
        return filename.split(".")[-1].lower() if "." in filename else "unknown"

    def _upload_to_blob_storage(
        self, file_content: bytes, filename: str, project_id: str, document_id: str
    ) -> str:
        """Upload document to blob storage."""
        raw_blob_name = f"raw-documents/{project_id}/{document_id}_{filename}"
        blob_client = self.blob_service_client.get_blob_client(
            container=app_config.AZURE_STORAGE_CONTAINER_NAME, blob=raw_blob_name
        )
        blob_client.upload_blob(file_content, overwrite=True)
        logger.info(f"Document uploaded to blob storage: {raw_blob_name}")
        return raw_blob_name

    def _update_document_blob_reference(
        self, document_id: str, raw_blob_name: str
    ) -> None:
        """Update document with blob storage reference."""
        with self._get_db_session() as db:
            document = db.query(Document).filter(Document.id == document_id).first()
            if document:
                document.original_blob_name = raw_blob_name
                document.status = "processing"
                db.commit()

    def _extract_text_from_document(
        self, file_content: bytes
    ) -> Tuple[str, Dict[int, int]]:
        """Extract text content and page mapping using Azure Document Intelligence.

        Returns:
            Tuple of (full_content, char_to_page_mapping) where char_to_page_mapping
            maps character positions to page numbers.
        """
        poller = self.doc_intel_client.begin_analyze_document(
            "prebuilt-read", AnalyzeDocumentRequest(bytes_source=file_content)
        )
        result = poller.result()

        full_content = result.content or ""
        char_to_page = {}

        # Build character position to page number mapping
        if result.pages:
            for page in result.pages:
                page_number = page.page_number
                # Get spans for this page (character ranges)
                if hasattr(page, "spans") and page.spans:
                    for span in page.spans:
                        for char_pos in range(span.offset, span.offset + span.length):
                            char_to_page[char_pos] = page_number

        return full_content, char_to_page

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

    def _update_document_processed_status(
        self, document_id: str, processed_blob_name: str
    ) -> None:
        """Update document status to processed."""
        with self._get_db_session() as db:
            document = db.query(Document).filter(Document.id == document_id).first()
            if document:
                document.processed_text_blob_name = processed_blob_name
                document.status = "processed"
                document.processed_at = datetime.now()
                db.commit()

    def _mark_document_indexed(self, document_id: str) -> None:
        """Mark document as indexed."""
        with self._get_db_session() as db:
            document = db.query(Document).filter(Document.id == document_id).first()
            if document:
                document.status = "indexed"
                document.search_indexed = True
                document.search_indexed_at = datetime.now()
                db.commit()

    def _mark_document_failed(self, document_id: str) -> None:
        """Mark document as failed."""
        with self._get_db_session() as db:
            document = db.query(Document).filter(Document.id == document_id).first()
            if document:
                document.status = "failed"
                db.commit()

    async def _create_segments_and_embeddings(
        self, document_id: str, content: str, char_to_page: Dict[int, int]
    ) -> None:
        """Create document segments and generate embeddings."""
        try:
            logger.info(
                f"Starting segment creation and embedding generation for document {document_id}"
            )

            # Split text into chunks
            chunks = self.text_splitter.split_text(content)
            logger.info(
                f"Split content into {len(chunks)} chunks for document {document_id}"
            )

            # Create segments in database with page information
            self._create_document_segments(document_id, chunks, content, char_to_page)
            logger.info(f"Created {len(chunks)} document segments in database")

            # Generate embeddings for all segments
            await self._generate_embeddings_for_segments(document_id)
            logger.info(
                f"Generated embeddings for all segments of document {document_id}"
            )

        except Exception as e:
            logger.error(
                f"Error creating segments and embeddings for document {document_id}: {e}"
            )
            raise

    def _create_document_segments(
        self,
        document_id: str,
        chunks: List[str],
        content: str,
        char_to_page: Dict[int, int],
    ) -> None:
        """Create document segments in database with page information."""
        with self._get_db_session() as db:
            search_start = 0
            for i, chunk in enumerate(chunks):
                # Find the position of this chunk in the original content
                # Strip the chunk to handle whitespace differences
                chunk_stripped = chunk.strip()
                chunk_start = content.find(chunk_stripped, search_start)

                if chunk_start == -1:
                    # Try finding without stripping
                    chunk_start = content.find(chunk, search_start)

                if chunk_start == -1:
                    # Last resort: search from beginning
                    chunk_start = content.find(chunk_stripped, 0)
                    if chunk_start == -1:
                        chunk_start = content.find(chunk, 0)

                # If still not found, use the last known position but log warning
                if chunk_start == -1:
                    logger.warning(
                        f"Could not find chunk {i} in content for document {document_id}. "
                        f"Using estimated position based on previous chunks."
                    )
                    chunk_start = search_start

                # Get the page number for the start of this chunk
                page_number = char_to_page.get(chunk_start)

                segment = DocumentSegment(
                    document_id=document_id,
                    segment_order=i,
                    content=chunk,
                    content_type="text",
                    page_number=page_number,
                )
                db.add(segment)

                # Update search position: move forward by chunk size minus overlap
                # to account for overlapping chunks
                if chunk_start != -1:
                    # Move to just past the non-overlapping part of this chunk
                    # This allows the next overlapping chunk to be found
                    search_start = chunk_start + max(1, len(chunk_stripped) - 200)

            db.commit()

    async def _generate_embeddings_for_segments(self, document_id: str) -> None:
        """Generate embeddings for document segments with rate limiting."""
        with self._get_db_session() as db:
            segments = self._get_segments_without_embeddings(db, document_id)

            if not segments:
                return

            # Process embeddings in batches with rate limiting
            batch_size = 200
            max_retries = 3

            for i in range(0, len(segments), batch_size):
                batch_segments = segments[i : i + batch_size]
                await self._process_embedding_batch(
                    db, batch_segments, i, batch_size, len(segments), max_retries
                )

    def _get_segments_without_embeddings(
        self, db: Session, document_id: str
    ) -> List[DocumentSegment]:
        """Get segments that don't have embeddings yet."""
        return (
            db.query(DocumentSegment)
            .filter(
                DocumentSegment.document_id == document_id,
                DocumentSegment.embedding_vector.is_(None),
            )
            .all()
        )

    async def _process_embedding_batch(
        self,
        db: Session,
        batch_segments: List[DocumentSegment],
        batch_index: int,
        batch_size: int,
        total_segments: int,
        max_retries: int,
    ) -> None:
        """Process a batch of embeddings with retry logic."""
        texts = [segment.content for segment in batch_segments]

        for attempt in range(max_retries):
            try:
                embeddings_list = await self.embeddings.aembed_documents(texts)

                # Store embeddings
                for segment, embedding in zip(batch_segments, embeddings_list):
                    segment.embedding_vector = embedding
                    segment.search_indexed = True
                    segment.search_indexed_at = datetime.now()

                db.commit()
                batch_num = batch_index // batch_size + 1
                total_batches = (total_segments + batch_size - 1) // batch_size
                logger.info(f"Processed embedding batch {batch_num}/{total_batches}")
                break  # Success, exit retry loop

            except Exception as e:
                if self._is_rate_limit_error(e):
                    wait_time = (2**attempt) * 5  # 5, 10, 20 seconds
                    logger.warning(
                        f"Rate limit hit, attempt {attempt + 1}, waiting {wait_time}s..."
                    )
                    await asyncio.sleep(wait_time)
                    if attempt == max_retries - 1:
                        raise  # Final attempt failed
                else:
                    raise  # Non-rate-limit error

    def _is_rate_limit_error(self, error: Exception) -> bool:
        """Check if error is a rate limit error."""
        error_str = str(error).lower()
        return "429" in str(error) or "rate limit" in error_str

    def list_documents(self, project_id: str, user_id: str) -> List[Document]:
        """List all documents for a project."""
        try:
            logger.info(f"Listing documents for project {project_id}")
            with self._get_db_session() as db:
                documents = (
                    db.query(Document)
                    .filter(
                        Document.project_id == project_id, Document.owner_id == user_id
                    )
                    .order_by(Document.uploaded_at.desc())
                    .all()
                )
                logger.info(
                    f"Found {len(documents)} documents for project {project_id}"
                )
                return documents
        except Exception as e:
            logger.error(f"Error listing documents for project {project_id}: {e}")
            raise

    def get_document(self, document_id: str, user_id: str) -> Optional[Document]:
        """Get a document by ID."""
        try:
            logger.info(f"Retrieving document: {document_id}")
            with self._get_db_session() as db:
                document = (
                    db.query(Document)
                    .filter(Document.id == document_id, Document.owner_id == user_id)
                    .first()
                )
                if document:
                    logger.info(f"Found document: {document_id} - {document.file_name}")
                else:
                    logger.info(f"Document not found: {document_id}")
                return document
        except Exception as e:
            logger.error(f"Error getting document {document_id}: {e}")
            raise

    async def search_documents(
        self, query: str, project_id: str, top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Search documents using PGVectorStore with proper filtering."""
        try:
            logger.info(
                f"Searching documents for project {project_id} with query: '{query[:100]}...' (top_k={top_k})"
            )

            # Get document IDs for the project
            document_ids = self._get_project_document_ids(project_id)
            if not document_ids:
                logger.info(f"No documents found for project {project_id}")
                return []

            logger.info(f"Found {len(document_ids)} documents in project {project_id}")

            # Create vector store and perform search
            vectorstore = await self._create_vector_store()
            similar_docs = await vectorstore.asimilarity_search_with_score(
                query, k=top_k, filter={"document_id": {"$in": document_ids}}
            )

            # Format and return results
            results = self._format_search_results(similar_docs)
            logger.info(f"Search completed: found {len(results)} relevant segments")
            return results

        except Exception as e:
            logger.error(f"Error searching documents for project {project_id}: {e}")
            raise

    def _get_project_document_ids(self, project_id: str) -> List[str]:
        """Get all document IDs for a project."""
        with self._get_db_session() as db:
            documents = (
                db.query(Document.id).filter(Document.project_id == project_id).all()
            )
            return [doc.id for doc in documents]

    def _get_project_language_code(self, project_id: str) -> str:
        """Get the language code for a project."""
        with self._get_db_session() as db:
            project = db.query(Project).filter(Project.id == project_id).first()
            return project.language_code if project else "en"

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
            metadata_columns=["id", "segment_order", "document_id", "page_number"],
        )

    def _format_search_results(
        self, similar_docs: List[Tuple[Any, float]]
    ) -> List[Dict[str, Any]]:
        """Format search results for API response."""
        search_results = []
        for doc, score in similar_docs:
            search_results.append(
                {
                    "id": doc.metadata.get("id", ""),
                    "content": doc.page_content,
                    "title": doc.metadata.get("title", ""),
                    "segment_order": doc.metadata.get("segment_order", 0),
                    "score": 1.0 - float(score),  # Convert distance to similarity score
                }
            )
        return search_results

    async def get_grounded_response(
        self,
        query: str,
        project_id: str,
        top_k: int = 5,
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """Get a grounded response using LangChain RAG with PGVectorStore."""
        try:
            logger.info(
                f"Getting grounded response for project {project_id} with query: '{query[:100]}...' (top_k={top_k})"
            )

            # Get project language code
            language_code = self._get_project_language_code(project_id)
            logger.info(
                f"Using language code: {language_code} for project {project_id}"
            )

            # Check if project has documents
            document_ids = self._get_project_document_ids(project_id)
            if not document_ids:
                logger.info(f"No documents found for project {project_id}")
                return {
                    "response": "No documents found for this project.",
                    "sources": [],
                    "query": query,
                }

            logger.info(f"Found {len(document_ids)} documents in project {project_id}")

            # Set up LLM and vector store
            llm = self._create_chat_llm()
            vectorstore = await self._create_vector_store()
            logger.info("Created LLM and vector store")

            # Create retriever and QA chain
            retriever = vectorstore.as_retriever(
                search_kwargs={
                    "k": top_k,
                    "filter": {"document_id": {"$in": document_ids}},
                }
            )

            qa_chain = self._create_qa_chain(
                llm, retriever, chat_history, language_code
            )
            logger.info("Created QA chain")

            # Get response
            result = qa_chain.invoke({"query": query})
            logger.info(
                f"Generated response with {len(result.get('source_documents', []))} source documents"
            )

            # Format response
            return {
                "response": result["result"],
                "sources": self._format_source_documents(
                    result.get("source_documents", [])
                ),
                "query": query,
            }

        except Exception as e:
            logger.error(
                f"Error getting grounded response for project {project_id}: {e}"
            )
            raise

    async def get_streaming_grounded_response(
        self,
        query: str,
        project_id: str,
        top_k: int = 5,
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Get a streaming grounded response using LangChain RAG with PGVectorStore."""
        try:
            logger.info(
                f"Getting streaming grounded response for project {project_id} with query: '{query[:100]}...' (top_k={top_k})"
            )

            # Get project language code
            language_code = self._get_project_language_code(project_id)
            logger.info(
                f"Using language code: {language_code} for project {project_id}"
            )

            # Check if project has documents
            document_ids = self._get_project_document_ids(project_id)
            if not document_ids:
                logger.info(f"No documents found for project {project_id}")
                yield {
                    "chunk": "No documents found for this project.",
                    "done": True,
                    "sources": [],
                }
                return

            logger.info(f"Found {len(document_ids)} documents in project {project_id}")

            # Yield initial chunk to show processing has started
            yield {"chunk": "", "done": False}

            # Set up vector store and get relevant documents first
            vectorstore = await self._create_vector_store()
            retriever = vectorstore.as_retriever(
                search_kwargs={
                    "k": top_k,
                    "filter": {"document_id": {"$in": document_ids}},
                }
            )

            # Get relevant documents for context
            relevant_docs = await retriever.ainvoke(query)
            logger.info(f"Retrieved {len(relevant_docs)} relevant documents")

            # Create context from relevant documents
            context_parts = []
            for i, doc in enumerate(relevant_docs, 1):
                title = doc.metadata.get("title", f"Document {i}")
                content = doc.page_content[:1000]  # Limit content length
                context_parts.append(f"Document {i} ({title}):\n{content}...")

            context = (
                "\n\n".join(context_parts)
                if context_parts
                else "No relevant documents found."
            )

            # Set up streaming LLM
            llm = self._create_streaming_chat_llm()
            logger.info("Created streaming LLM")

            # Build the prompt with context
            chat_history_context = self._build_chat_history_context(chat_history)
            prompt_template = f"""You are a helpful AI assistant that answers questions based on the provided documents.
Use the context from the documents to provide accurate and helpful responses.
If the context doesn't contain relevant information, say so clearly.
Always cite which document(s) you're referencing when possible.

IMPORTANT: Respond in {language_code} language. All your responses must be in {language_code}.

{chat_history_context}

Use the following pieces of context to answer the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer.

{context}

Question: {query}
Answer:"""

            # Stream the LLM response
            full_response = ""
            try:
                async for chunk in llm.astream(prompt_template):
                    if chunk.content:
                        chunk_text = chunk.content
                        full_response += chunk_text
                        yield {"chunk": chunk_text, "done": False}
                        # Small delay to prevent socket buffer overflow
                        await asyncio.sleep(0.001)

                # Yield the final response with sources
                sources = []
                for doc in relevant_docs:
                    document_id = doc.metadata.get("document_id", "")
                    doc_info = (
                        self._get_document_info(document_id)
                        if document_id
                        else {"title": ""}
                    )

                    page_number = doc.metadata.get("page_number")
                    preview_url = doc_info.get("preview_url")
                    content = doc.page_content

                    # Add page fragment for PDF viewer navigation
                    if preview_url and page_number:
                        preview_url = f"{preview_url}#page={page_number}"

                    sources.append(
                        {
                            "id": doc.metadata.get("id", ""),
                            "content": content,
                            "title": doc_info.get("title", ""),
                            "document_id": document_id,
                            "segment_order": doc.metadata.get("segment_order", 0),
                            "page_number": page_number,
                            "preview_url": preview_url,
                            "score": 1.0,
                        }
                    )

                yield {
                    "chunk": "",  # Empty chunk - client already has full response
                    "done": True,
                    "sources": sources,
                    "response": full_response,
                }

            except Exception as e:
                logger.error(f"Error during LLM streaming: {e}")
                yield {
                    "chunk": f"Error during response generation: {str(e)}",
                    "done": True,
                    "sources": [],
                }

        except Exception as e:
            logger.error(
                f"Error getting streaming grounded response for project {project_id}: {e}"
            )
            yield {"chunk": f"Error: {str(e)}", "done": True, "sources": []}

    def _create_chat_llm(self) -> AzureChatOpenAI:
        """Create Azure OpenAI chat LLM."""
        return AzureChatOpenAI(
            azure_deployment=app_config.AZURE_OPENAI_CHAT_DEPLOYMENT,
            azure_endpoint=app_config.AZURE_OPENAI_ENDPOINT,
            api_version="2024-12-01-preview",
            azure_ad_token_provider=self.token_provider,
            temperature=0,
        )

    def _create_streaming_chat_llm(self) -> AzureChatOpenAI:
        """Create Azure OpenAI chat LLM with streaming enabled."""
        return AzureChatOpenAI(
            azure_deployment=app_config.AZURE_OPENAI_CHAT_DEPLOYMENT,
            azure_endpoint=app_config.AZURE_OPENAI_ENDPOINT,
            api_version="2024-12-01-preview",
            azure_ad_token_provider=self.token_provider,
            temperature=0,
            streaming=True,
        )

    def _create_qa_chain(
        self,
        llm: AzureChatOpenAI,
        retriever,
        chat_history: Optional[List[Dict[str, str]]],
        language_code: str = "en",
    ) -> RetrievalQA:
        """Create QA chain with custom prompt."""
        chat_history_context = self._build_chat_history_context(chat_history)

        prompt_template = f"""You are a helpful AI assistant that answers questions based on the provided documents. 
Use the context from the documents to provide accurate and helpful responses. 
If the context doesn't contain relevant information, say so clearly.
Always cite which document(s) you're referencing when possible.

IMPORTANT: Respond in {language_code} language. All your responses must be in {language_code}.

{chat_history_context}

Use the following pieces of context to answer the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer.

{{context}}

Question: {{question}}
Answer:"""

        prompt = PromptTemplate(
            template=prompt_template, input_variables=["context", "question"]
        )

        return RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True,
            chain_type_kwargs={"prompt": prompt},
        )

    def _create_streaming_qa_chain(
        self,
        llm: AzureChatOpenAI,
        retriever,
        chat_history: Optional[List[Dict[str, str]]],
        language_code: str = "en",
    ) -> RetrievalQA:
        """Create streaming QA chain with custom prompt."""
        chat_history_context = self._build_chat_history_context(chat_history)

        prompt_template = f"""You are a helpful AI assistant that answers questions based on the provided documents.
Use the context from the documents to provide accurate and helpful responses.
If the context doesn't contain relevant information, say so clearly.
Always cite which document(s) you're referencing when possible.

IMPORTANT: Respond in {language_code} language. All your responses must be in {language_code}.

{chat_history_context}

Use the following pieces of context to answer the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer.

{{context}}

Question: {{question}}
Answer:"""

        prompt = PromptTemplate(
            template=prompt_template, input_variables=["context", "question"]
        )

        return RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True,
            chain_type_kwargs={"prompt": prompt},
        )

    def _format_source_documents(
        self, source_documents: List[Any]
    ) -> List[Dict[str, Any]]:
        """Format source documents for API response."""
        sources = []
        document_cache = {}  # Cache document info to avoid repeated DB queries

        for doc in source_documents:
            document_id = doc.metadata.get("document_id", "")

            # Get document info from cache or database
            if document_id not in document_cache:
                document_cache[document_id] = self._get_document_info(document_id)

            doc_info = document_cache[document_id]

            page_number = doc.metadata.get("page_number")
            preview_url = doc_info.get("preview_url")
            content = doc.page_content

            # Add page fragment for PDF viewer navigation
            if preview_url and page_number:
                preview_url = f"{preview_url}#page={page_number}"

            sources.append(
                {
                    "id": doc.metadata.get("id", ""),
                    "content": content,
                    "title": doc_info.get("title", ""),
                    "document_id": document_id,
                    "segment_order": doc.metadata.get("segment_order", 0),
                    "page_number": page_number,
                    "preview_url": preview_url,
                    "score": 1.0,  # PGVectorStore provides scores but not in this context
                }
            )
        return sources

    def _get_document_info(self, document_id: str) -> Dict[str, str]:
        """Get document information by ID."""
        with self._get_db_session() as db:
            document = db.query(Document).filter(Document.id == document_id).first()
            if document:
                # Use internal preview endpoint instead of direct blob URL
                preview_url = f"/v1/documents/{document_id}/preview"

                return {
                    "title": document.file_name,  # Use file_name as title
                    "preview_url": preview_url,
                }
            return {"title": "", "preview_url": None}

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

    def _build_context_from_search_results(
        self, search_results: List[Dict[str, Any]]
    ) -> str:
        """Build context string from search results."""
        if not search_results:
            return "No relevant documents found."

        context_parts = []
        for i, result in enumerate(search_results, 1):
            context_parts.append(
                f"Document {i} ({result['title']}):\n{result['content'][:1000]}..."
            )

        return "\n\n".join(context_parts)

    def _build_chat_history_context(
        self, chat_history: Optional[List[Dict[str, str]]]
    ) -> str:
        """Build context string from chat history."""
        if not chat_history:
            return ""

        history_parts = []
        for msg in chat_history[-6:]:  # Last 6 messages for context
            role = "User" if msg["role"] == "user" else "Assistant"
            history_parts.append(f"{role}: {msg['content']}")

        if history_parts:
            return f"Previous conversation:\n" + "\n".join(history_parts)
        return ""
