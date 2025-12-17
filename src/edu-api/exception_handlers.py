import logging

from edu_core.exceptions import NotFoundError, UsageLimitExceededError
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

logger = logging.getLogger(__name__)


async def not_found_error_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    """Handle NotFoundError exceptions."""
    logger.warning(
        f"Resource not found: {exc.message}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": 404,
        },
    )
    return JSONResponse(
        status_code=404,
        content={
            "error": {
                "message": exc.message,
                "status_code": 404,
            }
        },
    )


async def usage_limit_exceeded_error_handler(
    request: Request, exc: UsageLimitExceededError
) -> JSONResponse:
    """Handle UsageLimitExceededError exceptions."""
    logger.warning(
        f"Usage limit exceeded: {exc.message}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": 429,
            "usage_type": exc.usage_type,
            "current_count": exc.current_count,
            "limit": exc.limit,
        },
    )
    return JSONResponse(
        status_code=429,
        content={
            "error": {
                "message": exc.message,
                "status_code": 429,
                "usage_type": exc.usage_type,
                "current_count": exc.current_count,
                "limit": exc.limit,
            }
        },
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions with custom error format."""
    logger.warning(
        f"HTTP exception: {exc.detail}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": exc.status_code,
            "error_message": exc.detail,
            "client_ip": request.client.host if request.client else None,
        },
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


async def validation_error_handler(
    request: Request, exc: ValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors."""
    # Convert errors to JSON-serializable format
    errors = exc.errors()
    serializable_errors = []
    for error in errors:
        serializable_error = {
            "loc": list(error.get("loc", [])),
            "msg": str(error.get("msg", "")),
            "type": str(error.get("type", "")),
        }
        if "ctx" in error:
            # Convert context to string if it contains non-serializable data
            ctx = error["ctx"]
            if isinstance(ctx, dict):
                serializable_error["ctx"] = {
                    k: str(v)
                    if not isinstance(v, (str, int, float, bool, type(None)))
                    else v
                    for k, v in ctx.items()
                }
            else:
                serializable_error["ctx"] = str(ctx)
        serializable_errors.append(serializable_error)

    logger.warning(
        f"Validation error: {serializable_errors}",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": 422,
        },
    )
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "message": "Validation error",
                "status_code": 422,
                "details": serializable_errors,
            }
        },
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions."""
    logger.error(
        f"Unhandled exception: {type(exc).__name__}: {exc!s}",
        extra={
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "path": request.url.path,
            "method": request.method,
        },
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
