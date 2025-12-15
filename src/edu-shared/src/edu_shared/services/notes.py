"""CRUD service for managing notes."""

from contextlib import contextmanager
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from langchain_openai import AzureChatOpenAI

from edu_shared.agents.base import ContentAgentConfig
from edu_shared.agents.note_agent import NoteAgent
from edu_shared.db.models import Note, Project
from edu_shared.db.session import get_session_factory
from edu_shared.exceptions import NotFoundError
from edu_shared.schemas.notes import NoteDto
from edu_shared.services.search import SearchService

if TYPE_CHECKING:
    from edu_shared.services.queue import QueueService

class NoteService:
    """Service for managing notes."""

    def __init__(self) -> None:
        """Initialize the note service."""
        pass

    def create_note(
        self,
        project_id: str,
        title: str,
        content: str,
        description: str | None = None,
    ) -> NoteDto:
        """Create a new note.

        Args:
            project_id: The project ID
            title: The note title
            content: The note content
            description: Optional note description

        Returns:
            Created NoteDto
        """
        with self._get_db_session() as db:
            try:
                note = Note(
                    id=str(uuid4()),
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

                return self._model_to_dto(note)
            except Exception:
                db.rollback()
                raise

    def get_note(self, note_id: str, project_id: str) -> NoteDto:
        """Get a note by ID.

        Args:
            note_id: The note ID
            project_id: The project ID

        Returns:
            NoteDto

        Raises:
            NotFoundError: If note not found
        """
        with self._get_db_session() as db:
            try:
                note = (
                    db.query(Note)
                    .filter(Note.id == note_id, Note.project_id == project_id)
                    .first()
                )
                if not note:
                    raise NotFoundError(f"Note {note_id} not found")

                return self._model_to_dto(note)
            except NotFoundError:
                raise
            except Exception:
                raise

    def list_notes(self, project_id: str) -> list[NoteDto]:
        """List all notes for a project.

        Args:
            project_id: The project ID

        Returns:
            List of NoteDto instances
        """
        with self._get_db_session() as db:
            try:
                notes = (
                    db.query(Note)
                    .filter(Note.project_id == project_id)
                    .order_by(Note.created_at.desc())
                    .all()
                )
                return [self._model_to_dto(note) for note in notes]
            except Exception:
                raise

    def update_note(
        self,
        note_id: str,
        project_id: str,
        title: str | None = None,
        description: str | None = None,
        content: str | None = None,
    ) -> NoteDto:
        """Update a note.

        Args:
            note_id: The note ID
            project_id: The project ID
            title: Optional new title
            description: Optional new description
            content: Optional new content

        Returns:
            Updated NoteDto

        Raises:
            NotFoundError: If note not found
        """
        with self._get_db_session() as db:
            try:
                note = (
                    db.query(Note)
                    .filter(Note.id == note_id, Note.project_id == project_id)
                    .first()
                )
                if not note:
                    raise NotFoundError(f"Note {note_id} not found")

                if title is not None:
                    note.title = title
                if description is not None:
                    note.description = description
                if content is not None:
                    note.content = content
                note.updated_at = datetime.now()

                db.commit()
                db.refresh(note)

                return self._model_to_dto(note)
            except NotFoundError:
                raise
            except Exception:
                db.rollback()
                raise

    def delete_note(self, note_id: str, project_id: str) -> None:
        """Delete a note.

        Args:
            note_id: The note ID
            project_id: The project ID

        Raises:
            NotFoundError: If note not found
        """
        with self._get_db_session() as db:
            try:
                note = (
                    db.query(Note)
                    .filter(Note.id == note_id, Note.project_id == project_id)
                    .first()
                )
                if not note:
                    raise NotFoundError(f"Note {note_id} not found")

                db.delete(note)
                db.commit()
            except NotFoundError:
                raise
            except Exception:
                db.rollback()
                raise

    def _model_to_dto(self, note: Note) -> NoteDto:
        """Convert Note model to NoteDto."""
        return NoteDto(
            id=note.id,
            project_id=note.project_id,
            title=note.title,
            description=note.description,
            content=note.content,
            created_at=note.created_at,
            updated_at=note.updated_at,
        )

    async def generate_and_populate(
        self,
        note_id: str,
        project_id: str,
        search_service: SearchService,
        llm: AzureChatOpenAI | None = None,
        agent_config: ContentAgentConfig | None = None,
        topic: str | None = None,
        custom_instructions: str | None = None,
    ) -> NoteDto:
        """Generate note content using AI and populate an existing note.
        
        Args:
            note_id: The note ID to populate
            project_id: The project ID
            search_service: SearchService instance for RAG
            agent_config: ContentAgentConfig for AI generation
            topic: Optional topic for generation
            custom_instructions: Optional custom instructions
            
        Returns:
            Updated NoteDto
            
        Raises:
            NotFoundError: If note not found
        """
        with self._get_db_session() as db:
            try:
                # Find existing note
                note = db.query(Note).filter(
                    Note.id == note_id,
                    Note.project_id == project_id,
                ).first()
                if not note:
                    raise NotFoundError(f"Note {note_id} not found")

                # Get project language code
                project = db.query(Project).filter(Project.id == project_id).first()
                if not project:
                    raise NotFoundError(f"Project {project_id} not found")
                language_code = project.language_code

                # Generate note using AI
                note_agent = NoteAgent(
                    search_service=search_service,
                    llm=llm,
                    config=agent_config,
                )
                result = await note_agent.generate(
                    project_id=project_id,
                    topic=topic or "",
                    language_code=language_code,
                    custom_instructions=custom_instructions,
                )

                # Update note with generated content
                note.title = result.title
                note.description = result.description
                note.content = result.content
                note.updated_at = datetime.now()

                db.commit()
                db.refresh(note)

                return self._model_to_dto(note)
            except NotFoundError:
                raise
            except Exception:
                db.rollback()
                raise

    def queue_generation(
        self,
        note_id: str,
        project_id: str,
        queue_service: "QueueService",
        topic: str | None = None,
        custom_instructions: str | None = None,
        user_id: str | None = None,
    ) -> NoteDto:
        """Queue a note generation request to be processed by a worker.
        
        Args:
            note_id: The note ID to populate
            project_id: The project ID
            queue_service: QueueService instance to send the message
            topic: Optional topic for generation
            custom_instructions: Optional custom instructions
            user_id: Optional user ID for queue message
            
        Returns:
            Existing NoteDto (generation will happen asynchronously)
            
        Raises:
            NotFoundError: If note not found
        """
        from edu_shared.schemas.queue import (
            NoteGenerationData,
            QueueTaskMessage,
            TaskType,
        )

        # Verify note exists
        note = self.get_note(note_id=note_id, project_id=project_id)

        # Prepare task data
        task_data: NoteGenerationData = {
            "project_id": project_id,
            "note_id": note_id,
        }
        if topic:
            task_data["topic"] = topic
        if custom_instructions:
            task_data["custom_instructions"] = custom_instructions
        if user_id:
            task_data["user_id"] = user_id

        # Send message to queue
        task_message: QueueTaskMessage = {
            "type": TaskType.NOTE_GENERATION,
            "data": task_data,
        }
        queue_service.send_message(task_message)

        return note

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

