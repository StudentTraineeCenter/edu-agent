from datetime import datetime
from typing import Any

from edu_ai.agents.base import BaseContentAgent
from edu_db.models import Note, Project
from edu_core.exceptions import NotFoundError
from pydantic import BaseModel, Field


class NoteGenerationResult(BaseModel):
    """Model for note generation result."""

    title: str = Field(..., description="The title of the note")
    description: str = Field(..., description="The description of the note")
    content: str = Field(..., description="The content of the note")


class NoteAgent(BaseContentAgent[NoteGenerationResult]):
    @property
    def output_model(self):
        return NoteGenerationResult

    @property
    def prompt_template(self):
        return "note_prompt"

    async def generate_and_save(
        self,
        project_id: str,
        topic: str | None = None,
        custom_instructions: str | None = None,
        note_id: str | None = None,
        **kwargs: Any,
    ) -> Note:
        """Generate note content and save to the database.
        
        Args:
            project_id: The project ID
            topic: Optional topic for generation
            custom_instructions: Optional custom instructions
            note_id: The note ID to populate (required)
            
        Returns:
            Updated Note model
            
        Raises:
            NotFoundError: If note or project not found
            ValueError: If note_id is not provided
        """
        if not note_id:
            raise ValueError("note_id is required for note generation")
        
        with self._get_db_session() as db:
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
            result = await self.generate(
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

            db.flush()
            return note

