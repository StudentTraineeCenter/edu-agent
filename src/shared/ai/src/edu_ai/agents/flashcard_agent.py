from datetime import datetime
from typing import Any
from uuid import uuid4

from edu_db.models import Flashcard, FlashcardGroup, Project
from edu_core.exceptions import NotFoundError
from pydantic import BaseModel, Field

from edu_ai.agents.base import BaseContentAgent


class FlashcardGenerationResult(BaseModel):
    """Model for flashcard generation result."""

    question: str = Field(..., description="The flashcard question")
    answer: str = Field(..., description="The flashcard answer")
    difficulty_level: str = Field(
        ..., description="The difficulty level of the flashcard"
    )


class FlashcardGroupGenerationResult(BaseModel):
    """Model for flashcard generation result."""

    name: str = Field(..., description="The name of the flashcard group")
    description: str = Field(..., description="The description of the flashcard group")
    flashcards: list[FlashcardGenerationResult] = Field(
        ..., description="The flashcards of the flashcard group"
    )


class FlashcardAgent(BaseContentAgent[FlashcardGroupGenerationResult]):
    @property
    def output_model(self):
        return FlashcardGroupGenerationResult

    @property
    def prompt_template(self):
        return "flashcard_prompt"

    async def generate_and_save(
        self,
        project_id: str,
        topic: str | None = None,
        custom_instructions: str | None = None,
        group_id: str | None = None,
        count: int | None = None,
        difficulty: str | None = None,
        **kwargs: Any,
    ) -> FlashcardGroup:
        """Generate flashcards and save to the database.

        Args:
            project_id: The project ID
            topic: Optional topic for generation
            custom_instructions: Optional custom instructions
            group_id: The flashcard group ID to populate (required)
            count: Optional count of flashcards to generate
            difficulty: Optional difficulty level

        Returns:
            Updated FlashcardGroup model

        Raises:
            NotFoundError: If flashcard group or project not found
            ValueError: If group_id is not provided
        """
        if not group_id:
            raise ValueError("group_id is required for flashcard generation")

        with self._get_db_session() as db:
            # Find existing flashcard group
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                raise NotFoundError(f"Project {project_id} not found")

            language_code = project.language_code

            group = (
                db.query(FlashcardGroup)
                .filter(
                    FlashcardGroup.id == group_id,
                    FlashcardGroup.project_id == project_id,
                )
                .first()
            )
            if not group:
                raise NotFoundError(f"Flashcard group {group_id} not found")

            # Generate flashcards using AI
            kwargs = {}
            if count is not None:
                kwargs["count"] = count
            if difficulty is not None:
                kwargs["difficulty"] = difficulty

            result = await self.generate(
                project_id=project_id,
                topic=topic or "",
                language_code=language_code,
                custom_instructions=custom_instructions,
                **kwargs,
            )

            # Update group with generated name and description
            group.name = result.name
            group.description = result.description
            group.updated_at = datetime.now()
            db.flush()

            # Delete existing flashcards and create new ones
            db.query(Flashcard).filter(Flashcard.group_id == group_id).delete()

            # Save flashcards to database
            for position, flashcard_item in enumerate(result.flashcards):
                flashcard = Flashcard(
                    id=str(uuid4()),
                    group_id=group_id,
                    project_id=project_id,
                    question=flashcard_item.question,
                    answer=flashcard_item.answer,
                    difficulty_level=flashcard_item.difficulty_level,
                    position=position,
                    created_at=datetime.now(),
                )
                db.add(flashcard)

            db.flush()
            return group
