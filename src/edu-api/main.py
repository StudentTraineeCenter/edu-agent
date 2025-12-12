from sqlalchemy import text
from contextlib import asynccontextmanager
from pydantic import BaseModel
from fastapi import FastAPI
import uvicorn

from config import get_settings
from edu_shared.db.session import init_db
from routers import (
    projects_router,
    documents_router,
    chats_router,
    notes_router,
    quizzes_router,
    flashcard_groups_router,
    users_router,
)


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

        self.app = FastAPI(title=config.name, version=config.version, lifespan=lifespan)
        self.setup_routes()

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
        self.app.include_router(users_router)

    def run(self):
        """
        Starts the Uvicorn server.
        """
        uvicorn.run(self.app, host="0.0.0.0", port=self.config.port)


if __name__ == "__main__":
    config = ApiConfig(name="Edu API", port=8000)
    api = Api(config)
    api.run()
