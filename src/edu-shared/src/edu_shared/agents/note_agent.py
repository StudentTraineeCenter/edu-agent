from pydantic import BaseModel, Field
from edu_shared.agents.base import BaseContentAgent


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

