from datetime import datetime
from pydantic import BaseModel, Field

class FlashcardDto(BaseModel):

    model_config = {"from_attributes": True}


    id: str = Field(..., description="Unique ID of the flashcard")
    group_id: str = Field(..., description="ID of the flashcard group")        
    project_id: str = Field(..., description="ID of the project the flashcard belongs to")
    question: str = Field(..., description="Question of the flashcard")
    answer: str = Field(..., description="Answer of the flashcard")
    difficulty_level: str = Field(..., description="Difficulty level of the flashcard")
    position: int = Field(..., description="Position of the flashcard within the group")
    created_at: datetime = Field(..., description="Date and time the flashcard was created")
