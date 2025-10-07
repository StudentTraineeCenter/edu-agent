from contextlib import asynccontextmanager
import uvicorn
import logging
from fastapi import FastAPI
from scalar_fastapi import get_scalar_api_reference
from api.v1 import v1_router
from core.logger import get_logger


OPENAPI_URL = "/openapi.json"
APP_NAME = "EduAgent API"

logger = get_logger(__name__)

az_logger = logging.getLogger("azure")
az_logger.setLevel(logging.ERROR)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for FastAPI."""
    try:
        logger.info(f"Starting {APP_NAME} API...")

        # Azure Search infrastructure setup removed - using PostgreSQL vector search instead

        yield
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise
    finally:
        logger.info(f"Shutting down {APP_NAME} API...")


app = FastAPI(
    title=APP_NAME,
    openapi_url=OPENAPI_URL,
    docs_url=None,
    redoc_url=None,
    lifespan=lifespan,
)

app.include_router(router=v1_router, prefix="/v1")


@app.get("/health")
async def health_check():
    """Simple health check that doesn't require database"""
    return {"status": "healthy"}


@app.get("/", include_in_schema=False)
async def scalar_docs_ui():
    return get_scalar_api_reference(
        openapi_url=OPENAPI_URL,
        title=APP_NAME,
    )


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
