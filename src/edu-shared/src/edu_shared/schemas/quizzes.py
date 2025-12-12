from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class QuizDto(BaseModel):
    
    model_config = {"from_attributes": True}

    id: str = Field(..., description="Unique ID of the quiz")
    project_id: str = Field(..., description="ID of the project the quiz belongs to")
    name: str = Field(..., description="Name of the quiz")
    description: Optional[str] = Field(None, description="Description of the quiz")
    created_at: datetime = Field(..., description="Date and time the quiz was created")
    updated_at: datetime = Field(..., description="Date and time the quiz was updated")