from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UserDto(BaseModel):
    id: str = Field(..., description="Unique ID of the user")
    name: Optional[str] = Field(None, description="Name of the user")
    email: Optional[str] = Field(None, description="Email of the user")
    created_at: datetime = Field(..., description="Date and time the user was created")
    updated_at: datetime = Field(..., description="Date and time the user was updated")

    model_config = {"from_attributes": True}
