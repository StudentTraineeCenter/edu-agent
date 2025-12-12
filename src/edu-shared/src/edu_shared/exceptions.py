"""Exceptions for shared services."""


class NotFoundError(Exception):
    """Exception raised when a resource is not found."""

    def __init__(self, message: str = "Resource not found"):
        self.message = message
        super().__init__(self.message)

