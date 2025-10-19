from core.logger import get_logger
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

logger = get_logger(__name__)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions with custom error format."""
    # Check if it's one of our custom exceptions with details
    if hasattr(exc, "details") and exc.details:
        content = {
            "error": {
                "message": exc.detail,
                "status_code": exc.status_code,
                "details": exc.details,
            }
        }
    else:
        content = {
            "error": {
                "message": exc.detail,
                "status_code": exc.status_code,
            }
        }

    return JSONResponse(
        status_code=exc.status_code,
        content=content,
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions."""
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "message": "Internal server error",
                "status_code": 500,
            }
        },
    )
