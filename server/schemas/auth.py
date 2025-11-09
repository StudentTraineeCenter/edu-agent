from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UserDto(BaseModel):
    id: str
    name: Optional[str] = None
    email: Optional[str] = None
    azure_oid: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
