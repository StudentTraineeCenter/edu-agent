"""Exceptions for shared services."""


from typing import Optional
from fastapi import HTTPException


class NotFoundError(Exception):
    """Exception raised when a resource is not found."""

    def __init__(self, message: str = "Resource not found"):
        self.message = message
        super().__init__(self.message)


class UsageLimitExceededError(HTTPException):
    """Exception raised when user exceeds usage limit."""

    def __init__(
        self,
        usage_type: str,
        current_count: int,
        limit: int,
        message: Optional[str] = None,
    ):
        self.usage_type = usage_type
        self.current_count = current_count
        self.limit = limit
        if not message:
            message = (
                f"Usage limit exceeded for {usage_type}. "
                f"You have used {current_count} out of {limit} allowed per day."
            )
        super().__init__(
            status_code=429,
            detail=message,
        )