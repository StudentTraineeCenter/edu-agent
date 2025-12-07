import time
from typing import Callable

from core.logger import get_logger
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = get_logger(__name__)


class HTTPLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log HTTP requests and responses to Azure Monitor."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        # Extract request information
        method = request.method
        path = request.url.path
        query_params = dict(request.query_params)
        client_ip = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        # Log incoming request
        logger.info_structured(
            "HTTP request received",
            method=method,
            path=path,
            query_params=query_params,
            client_ip=client_ip,
            user_agent=user_agent,
            request_id=request.headers.get("x-request-id"),
        )

        # Process request
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            status_code = response.status_code

            # Log successful response
            logger.info_structured(
                "HTTP response sent",
                method=method,
                path=path,
                status_code=status_code,
                response_time_ms=round(process_time * 1000, 2),
                client_ip=client_ip,
                request_id=request.headers.get("x-request-id"),
            )

            # Add response time header
            response.headers["X-Process-Time"] = str(process_time)

            return response

        except Exception as exc:
            process_time = time.time() - start_time

            # Log error response
            logger.error_structured(
                "HTTP request failed",
                method=method,
                path=path,
                status_code=500,
                response_time_ms=round(process_time * 1000, 2),
                client_ip=client_ip,
                error_type=type(exc).__name__,
                error_message=str(exc),
                request_id=request.headers.get("x-request-id"),
                exc_info=True,
            )

            raise
