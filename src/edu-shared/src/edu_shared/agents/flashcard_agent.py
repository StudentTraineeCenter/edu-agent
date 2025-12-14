
from edu_shared.agents.base import BaseContentAgent
from pydantic import BaseModel, Field


class FlashcardGenerationResult(BaseModel):
    """Model for flashcard generation result."""

    question: str = Field(..., description="The flashcard question")
    answer: str = Field(..., description="The flashcard answer")
    difficulty_level: str = Field(..., description="The difficulty level of the flashcard")

class FlashcardGroupGenerationResult(BaseModel):
    """Model for flashcard generation result."""

    name: str = Field(..., description="The name of the flashcard group")
    description: str = Field(..., description="The description of the flashcard group")
    flashcards: list[FlashcardGenerationResult] = Field(..., description="The flashcards of the flashcard group")

class FlashcardAgent(BaseContentAgent[FlashcardGroupGenerationResult]):
    @property
    def output_model(self):
        return FlashcardGroupGenerationResult

    @property
    def prompt_template(self):
        return "flashcard_prompt"
