import logging
import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from api.endpoints import router as endpoints_router
from api.exception_handlers import general_exception_handler, http_exception_handler
from api.middleware.http_logging import HTTPLoggingMiddleware
from api.openapi import custom_openapi
from api.v1.router import v1_router
from core.config import app_config
from core.logger import get_logger

# Configure Azure Monitor OpenTelemetry early, before any other imports that might use logging
# This must be done before importing logger to ensure proper initialization
if os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING"):
    try:
        from azure.monitor.opentelemetry import configure_azure_monitor

        configure_azure_monitor(
            logger_name="edu_agent",  # Set namespace to avoid collecting SDK logs
            enable_live_metrics=True,
        )
    except ImportError:
        pass  # azure-monitor-opentelemetry not installed, continue without it

OPENAPI_URL = "/openapi.json"
APP_NAME = "EduAgent API"

logger = get_logger(__name__)

# Suppress uvicorn access logs - we handle HTTP logging via middleware
uvicorn_access_logger = logging.getLogger("uvicorn.access")
uvicorn_access_logger.setLevel(logging.WARNING)  # Suppress INFO level access logs

az_logger = logging.getLogger("azure")
az_logger.setLevel(logging.ERROR)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for FastAPI."""
    try:
        logger.info("starting %s api", APP_NAME)

        # Azure Search infrastructure setup removed - using PostgreSQL vector search instead

        yield
    except Exception as e:
        logger.error("error during startup: %s", e)
        raise
    finally:
        logger.info("shutting down %s api", APP_NAME)


app = FastAPI(
    title=APP_NAME,
    openapi_url=OPENAPI_URL,
    docs_url=None,
    redoc_url=None,
    lifespan=lifespan,
)


app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

app.openapi = lambda: custom_openapi(app)

# Add HTTP logging middleware first (outermost) to capture all requests/responses
app.add_middleware(HTTPLoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=app_config.CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router=v1_router, prefix="/v1")
app.include_router(router=endpoints_router)


if __name__ == "__main__":
    import asyncio

    import uvicorn

    # Disable uvicorn's default access logging - we handle it via middleware
    # This ensures all HTTP logs go through our structured logging to Azure Monitor
    config = uvicorn.Config(
        "main:app",
        host="0.0.0.0",
        port=8000,
        access_log=False,  # Disable uvicorn access logs - handled by HTTPLoggingMiddleware
        log_config=None,  # Use our custom logging configuration
    )
    server = uvicorn.Server(config)

    # Drive the coroutine directly; no loop_factory kwarg involved.
    asyncio.run(server.serve())
