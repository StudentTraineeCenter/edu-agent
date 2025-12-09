"""Service for managing notes with AI generation capabilities."""

import uuid
from contextlib import contextmanager
from datetime import datetime
from typing import AsyncGenerator, List, Optional

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import AzureChatOpenAI
from sqlalchemy.orm import Session

from core.agents.prompts_utils import render_prompt
from core.agents.search import SearchInterface
from core.config import app_config
from core.exceptions import BadRequestError, NotFoundError
from core.logger import get_logger
from db.models import Note, Project
from db.session import SessionLocal
from schemas.notes import (
    LENGTH_PREFERENCE_WORD_COUNT_MAP,
    MAX_DOCUMENT_CONTENT_LENGTH,
    NoteGenerationRequest,
    NoteGenerationResult,
    NoteProgressUpdate,
    SEARCH_TOP_K_WITH_TOPIC,
    SEARCH_TOP_K_WITHOUT_TOPIC,
)
from schemas.shared import (
    GenerationProgressUpdate,
    GenerationStatus,
    LengthPreference,
)

logger = get_logger(__name__)


class NoteService:
    """Service for managing notes with AI generation capabilities."""

    def __init__(self, search_interface: SearchInterface) -> None:
        """Initialize the note service.

        Args:
            search_interface: Search interface for document retrieval
        """
        self.search_interface = search_interface
        self.credential = DefaultAzureCredential()
        self.token_provider = get_bearer_token_provider(
            self.credential, "https://cognitiveservices.azure.com/.default"
        )

        self.llm = AzureChatOpenAI(
            azure_deployment=app_config.AZURE_OPENAI_CHAT_DEPLOYMENT,
            azure_endpoint=app_config.AZURE_OPENAI_ENDPOINT,
            api_version="2024-12-01-preview",
            azure_ad_token_provider=self.token_provider,
            temperature=0.7,
        )

        self.note_parser = JsonOutputParser(pydantic_object=NoteGenerationRequest)

    def _resolve_length_instruction(
        self, length: Optional[LengthPreference]
    ) -> str:
        """Resolve length preference to instruction string.
        
        Args:
            length: Length preference enum or None
            
        Returns:
            Length instruction string for prompt
        """
        if length is None:
            length = LengthPreference.NORMAL
        
        word_count = LENGTH_PREFERENCE_WORD_COUNT_MAP[length]
        if length == LengthPreference.LESS:
            return f" Keep the note concise (target: {word_count['min']}-{word_count['max']} words), focusing only on the most essential information with brief explanations."
        elif length == LengthPreference.MORE:
            return f" Create a comprehensive, detailed note (target: {word_count['min']}-{word_count['max']} words) with extensive coverage, multiple examples, detailed explanations, and thorough context."
        else:
            return f" Create a well-balanced note (target: {word_count['min']}-{word_count['max']} words) with appropriate detail and coverage."

    async def create_note_with_content(
        self,
        project_id: str,
        custom_instructions: Optional[str] = None,
        length: Optional[LengthPreference] = None,
    ) -> str:
        """Create a new note with auto-generated title, description, and markdown content.

        Args:
            project_id: The project ID
            custom_instructions: Optional custom instructions including topic, format, length, and context
            length: Length preference enum

        Returns:
            ID of the created note

        Raises:
            NotFoundError: If project not found
            ValueError: If no documents found or generation fails
        """
        with self._get_db_session() as db:
            try:
                logger.info_structured(
                    "creating note",
                    project_id=project_id,
                    length=length.value if length else None,
                    custom_instructions=custom_instructions[:100] if custom_instructions else None,
                )

                generated_content = await self._generate_note_content(
                    db=db,
                    project_id=project_id,
                    custom_instructions=custom_instructions,
                    length=length,
                )

                logger.info_structured(
                    "generated note content",
                    project_id=project_id,
                    title=generated_content.title[:100] if generated_content.title else None,
                )

                note = Note(
                    id=str(uuid.uuid4()),
                    project_id=project_id,
                    title=generated_content.title,
                    description=generated_content.description,
                    content=generated_content.content,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )

                db.add(note)
                db.commit()

                logger.info_structured(
                    "created note",
                    note_id=note.id,
                    project_id=project_id,
                )

                return str(note.id)
            except (NotFoundError, ValueError, BadRequestError):
                raise
            except Exception as e:
                logger.error_structured(
                    "error creating note",
                    project_id=project_id,
                    error=str(e),
                    exc_info=True,
                )
                raise

    async def create_note_with_content_stream(
        self,
        project_id: str,
        custom_instructions: Optional[str] = None,
        length: Optional[LengthPreference] = None,
    ) -> AsyncGenerator[dict, None]:
        """Create a note with streaming progress updates.

        Args:
            project_id: The project ID
            custom_instructions: Optional custom instructions including topic, format, length, and context
            length: Length preference enum

        Yields:
            Progress update dictionaries with status and message
        """
        try:
            yield GenerationProgressUpdate(
                status=GenerationStatus.SEARCHING
            ).model_dump(exclude_none=True)

            with self._get_db_session() as db:
                project = db.query(Project).filter(Project.id == project_id).first()
                if not project:
                    yield GenerationProgressUpdate(
                        status=GenerationStatus.DONE,
                        error=f"Project {project_id} not found",
                    ).model_dump(exclude_none=True)
                    return

                yield GenerationProgressUpdate(
                    status=GenerationStatus.STRUCTURING
                ).model_dump(exclude_none=True)

                document_content = await self._get_project_documents_content(
                    db=db,
                    project_id=project_id,
                    topic=custom_instructions,
                )
                if not document_content:
                    error_msg = (
                        f"No documents found related to '{custom_instructions}'. Please upload relevant documents or try a different topic."
                        if custom_instructions
                        else "No documents found in project. Please upload documents first."
                    )
                    yield GenerationProgressUpdate(
                        status=GenerationStatus.DONE,
                        error=error_msg,
                    ).model_dump(exclude_none=True)
                    return

                yield GenerationProgressUpdate(
                    status=GenerationStatus.WRITING
                ).model_dump(exclude_none=True)

                generated_content = await self._generate_note_content(
                    db=db,
                    project_id=project_id,
                    custom_instructions=custom_instructions,
                    length=length,
                )

                note = Note(
                    id=str(uuid.uuid4()),
                    project_id=project_id,
                    title=generated_content.title,
                    description=generated_content.description,
                    content=generated_content.content,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
                db.add(note)
                db.commit()
                db.refresh(note)

                logger.info_structured(
                    "created note",
                    note_id=note.id,
                    project_id=project_id,
                )

                yield NoteProgressUpdate(
                    status=GenerationStatus.DONE,
                    note_id=str(note.id),
                ).model_dump(exclude_none=True)

        except (NotFoundError, ValueError, BadRequestError) as e:
            logger.error_structured(
                "error creating note",
                project_id=project_id,
                error=str(e),
            )
            yield GenerationProgressUpdate(
                status=GenerationStatus.DONE,
                error=str(e),
            ).model_dump(exclude_none=True)
        except Exception as e:
            logger.error_structured(
                "error creating note",
                project_id=project_id,
                error=str(e),
                exc_info=True,
            )
            yield GenerationProgressUpdate(
                status=GenerationStatus.DONE,
                error="Failed to create note. Please try again.",
            ).model_dump(exclude_none=True)

    def get_notes(self, project_id: str) -> List[Note]:
        """Get all notes for a project.

        Args:
            project_id: The project ID

        Returns:
            List of Note model instances
        """
        with self._get_db_session() as db:
            try:
                logger.info_structured("getting notes", project_id=project_id)

                notes = (
                    db.query(Note)
                    .filter(Note.project_id == project_id)
                    .order_by(Note.created_at.desc())
                    .all()
                )

                logger.info_structured("found notes", count=len(notes), project_id=project_id)
                return notes
            except Exception as e:
                logger.error_structured("error getting notes", project_id=project_id, error=str(e), exc_info=True)
                raise

    def get_note(self, note_id: str) -> Optional[Note]:
        """Get a specific note by ID.

        Args:
            note_id: The note ID

        Returns:
            Note model instance or None if not found
        """
        with self._get_db_session() as db:
            try:
                logger.info_structured("getting note", note_id=note_id)

                note = db.query(Note).filter(Note.id == note_id).first()

                if note:
                    logger.info_structured("found note", note_id=note_id)
                else:
                    logger.info_structured("note not found", note_id=note_id)

                return note
            except Exception as e:
                logger.error_structured("error getting note", note_id=note_id, error=str(e), exc_info=True)
                raise

    def delete_note(self, note_id: str) -> bool:
        """Delete a note.

        Args:
            note_id: The note ID

        Returns:
            True if deleted successfully, False if not found
        """
        with self._get_db_session() as db:
            try:
                logger.info_structured("deleting note", note_id=note_id)

                note = db.query(Note).filter(Note.id == note_id).first()

                if not note:
                    logger.warning_structured("note not found", note_id=note_id)
                    return False

                db.delete(note)
                db.commit()

                logger.info_structured("deleted note", note_id=note_id)
                return True
            except Exception as e:
                logger.error_structured("error deleting note", note_id=note_id, error=str(e), exc_info=True)
                raise

    def update_note(
        self,
        note_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        content: Optional[str] = None,
    ) -> Optional[Note]:
        """Update a note.

        Args:
            note_id: The note ID
            title: Optional new title
            description: Optional new description
            content: Optional new content

        Returns:
            Updated Note model instance or None if not found
        """
        with self._get_db_session() as db:
            try:
                logger.info_structured("updating note", note_id=note_id)

                note = db.query(Note).filter(Note.id == note_id).first()
                if not note:
                    logger.warning_structured("note not found", note_id=note_id)
                    return None

                if title is not None:
                    note.title = title
                if description is not None:
                    note.description = description
                if content is not None:
                    note.content = content

                note.updated_at = datetime.now()

                db.commit()
                db.refresh(note)

                logger.info_structured("updated note", note_id=note_id)

                return note
            except Exception as e:
                logger.error_structured("error updating note", note_id=note_id, error=str(e), exc_info=True)
                raise

    async def _generate_note_content(
        self,
        db: Session,
        project_id: str,
        custom_instructions: Optional[str] = None,
        length: Optional[LengthPreference] = None,
    ) -> NoteGenerationResult:
        """Generate note title, description, and markdown content.

        Args:
            db: Database session
            project_id: The project ID
            custom_instructions: Optional custom instructions including topic, format, length, and context
            length: Length preference enum

        Returns:
            NoteGenerationResult containing title, description, and content

        Raises:
            NotFoundError: If project not found
            ValueError: If no documents available
        """
        try:
            logger.info_structured(
                "generating note content",
                project_id=project_id,
                length=length.value if length else None,
            )

            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                raise NotFoundError(f"Project {project_id} not found")

            language_code = project.language_code
            logger.info_structured(
                "using language code",
                language_code=language_code,
                project_id=project_id,
            )

            document_content = await self._get_project_documents_content(
                db=db,
                project_id=project_id,
                topic=custom_instructions,
            )
            if not document_content:
                error_msg = (
                    f"No documents found related to '{custom_instructions}'. Please upload relevant documents or try a different topic."
                    if custom_instructions
                    else "No documents found in project. Please upload documents first."
                )
                raise ValueError(error_msg)

            logger.info_structured(
                "found document content",
                document_content_length=len(document_content),
                project_id=project_id,
            )

            length_instruction = self._resolve_length_instruction(length)

            prompt = render_prompt(
                "note_prompt",
                document_content=document_content[:MAX_DOCUMENT_CONTENT_LENGTH],
                custom_instructions=(custom_instructions
                or "Generate a comprehensive study note covering key concepts, definitions, and important details.")
                + length_instruction,
                language_code=language_code,
                format_instructions=self.note_parser.get_format_instructions(),
            )

            response = await self.llm.ainvoke(prompt)
            parsed_dict = self.note_parser.parse(response.content)
            generation_request = NoteGenerationRequest(**parsed_dict)

            return NoteGenerationResult(
                title=generation_request.title,
                description=generation_request.description,
                content=generation_request.content,
            )
        except (NotFoundError, ValueError):
            raise
        except Exception as e:
            logger.error_structured(
                "error generating note content",
                project_id=project_id,
                error=str(e),
                exc_info=True,
            )
            raise

    async def _get_project_documents_content(
        self,
        db: Session,
        project_id: str,
        topic: Optional[str] = None,
    ) -> str:
        """Get document content for a project, optionally filtered by topic.

        Args:
            db: Database session
            project_id: The project ID
            topic: Optional topic to filter documents by

        Returns:
            Combined document content as string
        """
        try:
            query = topic or ""
            top_k = (
                SEARCH_TOP_K_WITH_TOPIC if topic else SEARCH_TOP_K_WITHOUT_TOPIC
            )

            logger.info_structured(
                "searching documents",
                project_id=project_id,
                has_topic=bool(topic),
                top_k=top_k,
            )

            search_results = await self.search_interface.search_documents(
                query=query,
                project_id=project_id,
                top_k=top_k,
            )

            if not search_results:
                logger.warning_structured(
                    "no search results found",
                    project_id=project_id,
                    has_topic=bool(topic),
                )
                return ""

            content = "\n\n".join(result.content for result in search_results)
            logger.info_structured(
                "retrieved document content",
                project_id=project_id,
                result_count=len(search_results),
                content_length=len(content),
            )
            return content
        except Exception as e:
            logger.error_structured(
                "error getting project documents content",
                project_id=project_id,
                error=str(e),
                exc_info=True,
            )
            return ""


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
