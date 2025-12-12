"""CRUD service for managing notes."""

from contextlib import contextmanager
from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from edu_shared.db.models import Note
from edu_shared.db.session import get_session_factory
from edu_shared.schemas.notes import NoteDto
from edu_shared.exceptions import NotFoundError
from edu_shared.agents.note_agent import NoteAgent
from edu_shared.agents.base import ContentAgentConfig
from edu_shared.services.search import SearchService


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
        description: Optional[str] = None,
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
            except Exception as e:
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
            except Exception as e:
                raise

    def list_notes(self, project_id: str) -> List[NoteDto]:
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
            except Exception as e:
                raise

    def update_note(
        self,
        note_id: str,
        project_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        content: Optional[str] = None,
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
            except Exception as e:
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
            except Exception as e:
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
        agent_config: ContentAgentConfig,
        topic: Optional[str] = None,
        custom_instructions: Optional[str] = None,
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

                # Generate note using AI
                note_agent = NoteAgent(config=agent_config, search_service=search_service)
                result = await note_agent.generate(
                    project_id=project_id,
                    topic=topic or "",
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
            except Exception as e:
                db.rollback()
                raise

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

