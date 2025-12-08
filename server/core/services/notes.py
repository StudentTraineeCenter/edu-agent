"""Service for managing notes with AI generation capabilities."""

import uuid
from contextlib import contextmanager
from datetime import datetime
from typing import AsyncGenerator, List, Optional

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import AzureChatOpenAI
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from core.agents.prompts_utils import render_prompt
from core.agents.search import SearchInterface
from core.config import app_config
from core.logger import get_logger
from db.models import Note, Project
from db.session import SessionLocal

logger = get_logger(__name__)


class NoteGenerationRequest(BaseModel):
    """Pydantic model for note generation request."""

    title: str = Field(description="Generated title for the note")
    description: str = Field(description="Generated description for the note")
    content: str = Field(description="Generated markdown content for the note")


class NoteGenerationResult(BaseModel):
    """Model for note generation result."""

    title: str
    description: str
    content: str


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

    async def create_note_with_content(
        self,
        project_id: str,
        user_prompt: Optional[str] = None,
        length: Optional[str] = None,
    ) -> str:
        """Create a new note with auto-generated title, description, and markdown content.

        Args:
            project_id: The project ID
            user_prompt: Optional user instructions for generation (topic)

        Returns:
            ID of the created note

        Raises:
            ValueError: If no documents found or generation fails
        """
        with self._get_db_session() as db:
            try:
                logger.info_structured("creating note", project_id=project_id, user_prompt=user_prompt[:100] if user_prompt else None)

                # Generate all content using LangChain directly
                generated_content = await self._generate_note_content(
                    db=db,
                    project_id=project_id,
                    user_prompt=user_prompt,
                    length=length,
                )

                title = generated_content.title
                description = generated_content.description
                content = generated_content.content

                logger.info_structured("creating note", title=title[:100] if title else None, project_id=project_id)

                note = Note(
                    id=str(uuid.uuid4()),
                    project_id=project_id,
                    title=title,
                    description=description,
                    content=content,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )

                db.add(note)
                db.commit()

                logger.info_structured("created note", note_id=note.id, project_id=project_id)

                return str(note.id)
            except ValueError:
                raise
            except Exception as e:
                logger.error_structured("error creating note", project_id=project_id, error=str(e), exc_info=True)
                raise

    async def create_note_with_content_stream(
        self,
        project_id: str,
        user_prompt: Optional[str] = None,
        length: Optional[str] = None,
    ) -> AsyncGenerator[dict, None]:
        """Create a note with streaming progress updates.

        Args:
            project_id: The project ID
            user_prompt: Optional user instructions for generation (topic)

        Yields:
            Progress update dictionaries with status and message
        """
        try:
            yield {"status": "searching", "message": "Searching documents..."}

            with self._get_db_session() as db:
                # Get project language code
                project = db.query(Project).filter(Project.id == project_id).first()
                if not project:
                    yield {
                        "status": "done",
                        "message": "Error: Project not found",
                        "error": f"Project {project_id} not found",
                    }
                    return

                language_code = project.language_code

                # Extract topic from user_prompt if provided
                topic = None
                if user_prompt:
                    topic = user_prompt

                yield {"status": "structuring", "message": "Structuring content..."}

                # Get project documents content
                document_content = await self._get_project_documents_content(
                    project_id, topic=topic
                )
                if not document_content:
                    if topic:
                        error_msg = f"No documents found related to '{topic}'. Please upload relevant documents or try a different topic."
                    else:
                        error_msg = "No documents found in project. Please upload documents first."
                    yield {
                        "status": "done",
                        "message": "Error: No documents found",
                        "error": error_msg,
                    }
                    return

                yield {"status": "writing", "message": "Writing note..."}

                # Generate content
                generated_content = await self._generate_note_content(
                    db=db,
                    project_id=project_id,
                    user_prompt=user_prompt,
                    length=length,
                )

                title = generated_content.title
                description = generated_content.description
                content = generated_content.content

                # Create note in database
                note = Note(
                    id=str(uuid.uuid4()),
                    project_id=project_id,
                    title=title,
                    description=description,
                    content=content,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
                db.add(note)
                db.commit()
                db.refresh(note)

                logger.info_structured("created note", note_id=note.id, project_id=project_id)

                yield {
                    "status": "done",
                    "message": "Note created successfully",
                    "note_id": str(note.id),
                }

        except ValueError as e:
            logger.error_structured("error creating note", project_id=project_id, error=str(e))
            yield {
                "status": "done",
                "message": "Error creating note",
                "error": str(e),
            }
        except Exception as e:
            logger.error_structured("error creating note", project_id=project_id, error=str(e), exc_info=True)
            yield {
                "status": "done",
                "message": "Error creating note",
                "error": "Failed to create note. Please try again.",
            }

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
        user_prompt: Optional[str] = None,
        length: Optional[str] = None,
    ) -> NoteGenerationResult:
        """Generate note title, description, and markdown content.

        Args:
            db: Database session
            project_id: The project ID
            user_prompt: Optional user instructions (topic)

        Returns:
            NoteGenerationResult containing title, description, and content

        Raises:
            ValueError: If project not found or no documents available
        """
        try:
            logger.info_structured("generating note content", project_id=project_id)

            project = db.query(Project).filter(Project.id == project_id).first()

            if not project:
                raise ValueError(f"Project {project_id} not found")

            language_code = project.language_code
            logger.info(
                f"using language_code={language_code} for project_id={project_id}"
            )

            # Extract topic from user_prompt if provided
            topic = None
            if user_prompt:
                topic = user_prompt

            # Get project documents content, optionally filtered by topic
            document_content = await self._get_project_documents_content(
                project_id, topic=topic
            )
            if not document_content:
                if topic:
                    raise ValueError(
                        f"No documents found related to '{topic}'. Please upload relevant documents or try a different topic."
                    )
                raise ValueError(
                    "No documents found in project. Please upload documents first."
                )

            logger.info(
                f"found {len(document_content)} chars of content in project_id={project_id}"
            )

            # Build length instruction with concrete targets
            length_instruction = ""
            if length == "less":
                length_instruction = " Keep the note concise (target: 500-800 words), focusing only on the most essential information with brief explanations."
            elif length == "more":
                length_instruction = " Create a comprehensive, detailed note (target: 2000-3000 words) with extensive coverage, multiple examples, detailed explanations, and thorough context."
            # "normal" or None uses default behavior (target: 1000-1500 words)

            # Build the prompt using Jinja2 template
            prompt = render_prompt(
                "note_prompt",
                document_content=document_content[
                    :8000
                ],  # Limit content to avoid token limits
                user_prompt=(user_prompt
                or "Generate a comprehensive study note covering key concepts, definitions, and important details.")
                + length_instruction,
                language_code=language_code,
                format_instructions=self.note_parser.get_format_instructions(),
            )

            # Generate content
            response = await self.llm.ainvoke(prompt)

            # Parse the response
            parsed_dict = self.note_parser.parse(response.content)
            generation_request = NoteGenerationRequest(**parsed_dict)

            return NoteGenerationResult(
                title=generation_request.title,
                description=generation_request.description,
                content=generation_request.content,
            )
        except ValueError:
            raise
        except Exception as e:
            logger.error(
                f"error generating note content for project_id={project_id}: {e}"
            )
            raise

    async def _get_project_documents_content(
        self, project_id: str, topic: Optional[str] = None
    ) -> str:
        """Get document content for a project, optionally filtered by topic.

        Args:
            project_id: The project ID
            topic: Optional topic to filter documents by

        Returns:
            Combined document content as string
        """
        try:
            # If topic is provided, search for relevant documents
            # Otherwise, get all content
            query = topic if topic else ""
            top_k = 50 if topic else 100  # Fewer results when filtering by topic

            search_results = await self.search_interface.search_documents(
                query=query,
                project_id=project_id,
                top_k=top_k,
            )

            if not search_results:
                return ""

            # Combine all content
            content_parts = []
            for result in search_results:
                content_parts.append(result.content)

            return "\n\n".join(content_parts)
        except Exception as e:
            logger.error(
                f"error getting project documents content for project_id={project_id}: {e}"
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
