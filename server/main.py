import logging
from contextlib import asynccontextmanager

import uvicorn
from api.endpoints import router as endpoints_router
from api.exception_handlers import general_exception_handler, http_exception_handler
from api.openapi import custom_openapi
from api.v1.router import v1_router
from core.logger import get_logger
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

OPENAPI_URL = "/openapi.json"
APP_NAME = "EduAgent API"

logger = get_logger(__name__)

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router=v1_router, prefix="/v1")
app.include_router(router=endpoints_router)


if __name__ == "__main__":
    import asyncio

    import uvicorn

    config = uvicorn.Config("main:app", host="0.0.0.0", port=8000)
    server = uvicorn.Server(config)

    # Drive the coroutine directly; no loop_factory kwarg involved.
    asyncio.run(server.serve())
