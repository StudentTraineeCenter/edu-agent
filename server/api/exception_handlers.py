from core.logger import get_logger
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

logger = get_logger(__name__)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions with custom error format."""
    # Log HTTP exception to Azure Monitor
    logger.warning_structured(
        "HTTP exception",
        method=request.method,
        path=request.url.path,
        status_code=exc.status_code,
        error_message=exc.detail,
        client_ip=request.client.host if request.client else None,
        request_id=request.headers.get("x-request-id"),
    )

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
    logger.error_structured(
        "Unhandled exception",
        exception_type=type(exc).__name__,
        exception_message=str(exc),
        path=request.url.path,
        method=request.method,
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "message": "Internal server error",
                "status_code": 500,
            }
        },
    )
