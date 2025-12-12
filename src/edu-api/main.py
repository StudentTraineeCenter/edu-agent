from sqlalchemy import text
from contextlib import asynccontextmanager
from pydantic import BaseModel
from fastapi import FastAPI, Depends
import uvicorn

from config import get_settings
from edu_shared.db.session import init_db, get_db


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
        async def health_check(db=Depends(get_db)):
            db.execute(text("SELECT 1"))  # Simple query to check DB connectivity
            return {"status": "healthy", "api": self.config.name}

    def run(self):
        """
        Starts the Uvicorn server.
        """
        uvicorn.run(self.app, host="0.0.0.0", port=self.config.port)


if __name__ == "__main__":
    config = ApiConfig(name="Edu API", port=8000)
    api = Api(config)
    api.run()
