from datetime import datetime
from pydantic import BaseModel


class UserDto(BaseModel):
    id: str
    name: str
    email: str
    azure_oid: str
    created_at: datetime

    class Config:
        from_attributes = True
