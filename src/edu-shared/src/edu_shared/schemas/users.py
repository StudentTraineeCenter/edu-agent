from datetime import datetime

from pydantic import BaseModel, Field


class UserDto(BaseModel):
    id: str = Field(..., description="Unique ID of the user")
    name: str | None = Field(None, description="Name of the user")
    email: str | None = Field(None, description="Email of the user")
    created_at: datetime = Field(..., description="Date and time the user was created")
    updated_at: datetime = Field(..., description="Date and time the user was updated")

    model_config = {"from_attributes": True}
