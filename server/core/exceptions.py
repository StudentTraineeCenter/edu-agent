from typing import Optional

from fastapi import HTTPException


class NotFoundError(HTTPException):
    """Exception raised when a resource is not found."""

    def __init__(
        self, message: str = "Resource not found", details: Optional[dict] = None
    ):
        self.details = details or {}
        super().__init__(status_code=404, detail=message)


class BadRequestError(HTTPException):
    """Exception raised for bad request errors."""

    def __init__(self, message: str = "Bad request", details: Optional[dict] = None):
        self.details = details or {}
        super().__init__(status_code=400, detail=message)


class UnauthorizedError(HTTPException):
    """Exception raised for unauthorized access."""

    def __init__(self, message: str = "Unauthorized", details: Optional[dict] = None):
        self.details = details or {}
        super().__init__(status_code=401, detail=message)


class ForbiddenError(HTTPException):
    """Exception raised for forbidden access."""

    def __init__(self, message: str = "Forbidden", details: Optional[dict] = None):
        self.details = details or {}
        super().__init__(status_code=403, detail=message)


class ConflictError(HTTPException):
    """Exception raised for resource conflicts."""

    def __init__(
        self, message: str = "Resource conflict", details: Optional[dict] = None
    ):
        self.details = details or {}
        super().__init__(status_code=409, detail=message)


class ValidationError(HTTPException):
    """Exception raised for validation errors."""

    def __init__(
        self, message: str = "Validation error", details: Optional[dict] = None
    ):
        self.details = details or {}
        super().__init__(status_code=422, detail=message)


class InternalServerError(HTTPException):
    """Exception raised for internal server errors."""

    def __init__(
        self, message: str = "Internal server error", details: Optional[dict] = None
    ):
        self.details = details or {}
        super().__init__(status_code=500, detail=message)


class ServiceUnavailableError(HTTPException):
    """Exception raised when a service is unavailable."""

    def __init__(
        self, message: str = "Service unavailable", details: Optional[dict] = None
    ):
        self.details = details or {}
        super().__init__(status_code=503, detail=message)


class TooManyRequestsError(HTTPException):
    """Exception raised for rate limiting."""

    def __init__(
        self, message: str = "Too many requests", details: Optional[dict] = None
    ):
        self.details = details or {}
        super().__init__(status_code=429, detail=message)


class UsageLimitExceeded(HTTPException):
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
