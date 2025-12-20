from contextlib import asynccontextmanager

import uvicorn
from config import get_settings
from edu_core.exceptions import NotFoundError, UsageLimitExceededError
from edu_db.session import init_db
from exception_handlers import (
    general_exception_handler,
    http_exception_handler,
    not_found_error_handler,
    usage_limit_exceeded_error_handler,
    validation_error_handler,
)
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ValidationError
from routers import (
    auth_router,
    chats_router,
    documents_router,
    flashcard_groups_router,
    mind_maps_router,
    notes_router,
    practice_records_router,
    projects_router,
    quizzes_router,
    study_sessions_global_router,
    study_sessions_router,
    study_plans_router,
    usage_router,
    users_router,
)
from scalar_fastapi import get_scalar_api_reference


class ApiConfig(BaseModel):
    name: str
    port: int
    version: str = "0.1.0"


class Api:
    def __init__(self, config: ApiConfig):
        self.config = config

        # Lifecycle manager for startup/shutdown events
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            settings = get_settings()
            # Initialize the database
            init_db(settings.database_url)
            print(
                f"[{self.config.name}] Startup: Ready to serve on port {self.config.port}"
            )
            yield
            print(f"[{self.config.name}] Shutdown: cleanup complete.")

        self.app = FastAPI(
            title=config.name,
            version=config.version,
            lifespan=lifespan,
            docs_url=None,
            redoc_url=None,
        )
        self.setup_cors()
        self.setup_exception_handlers()
        self.setup_routes()
        self.setup_openapi()

    def setup_cors(self):
        """Configure CORS middleware."""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Allow all origins
            allow_credentials=True,
            allow_methods=["*"],  # Allow all methods
            allow_headers=["*"],  # Allow all headers
        )

    def setup_exception_handlers(self):
        """Register exception handlers."""
        self.app.add_exception_handler(NotFoundError, not_found_error_handler)
        self.app.add_exception_handler(
            UsageLimitExceededError, usage_limit_exceeded_error_handler
        )
        self.app.add_exception_handler(HTTPException, http_exception_handler)
        self.app.add_exception_handler(ValidationError, validation_error_handler)
        self.app.add_exception_handler(Exception, general_exception_handler)

    def setup_routes(self):
        @self.app.get("/health")
        async def health_check():
            return {"status": "healthy", "api": self.config.name}

        # Register all routers
        self.app.include_router(projects_router)
        self.app.include_router(documents_router)
        self.app.include_router(chats_router)
        self.app.include_router(notes_router)
        self.app.include_router(quizzes_router)
        self.app.include_router(flashcard_groups_router)
        self.app.include_router(practice_records_router)
        self.app.include_router(mind_maps_router)
        self.app.include_router(study_sessions_router)
        self.app.include_router(study_sessions_global_router)
        self.app.include_router(study_plans_router)
        self.app.include_router(usage_router)
        self.app.include_router(users_router)
        self.app.include_router(auth_router)

    def setup_openapi(self):
        """Setup Scalar OpenAPI documentation UI."""

        @self.app.get("/", include_in_schema=False)
        async def scalar_docs_ui():
            """Scalar API documentation UI."""
            return get_scalar_api_reference(
                openapi_url=self.app.openapi_url,
                title=self.app.title,
            )

    def run(self):
        """
        Starts the Uvicorn server.
        """
        uvicorn.run(self.app, host="0.0.0.0", port=self.config.port)


if __name__ == "__main__":
    config = ApiConfig(name="Edu API", port=8000)
    api = Api(config)
    api.run()
