from contextlib import asynccontextmanager
from pydantic import BaseModel
from fastapi import FastAPI
import uvicorn


class ApiConfig(BaseModel):
    name: str
    port: int
    version: str = "0.1.0"


class Api:
    # 🌟 NEW: Static Framework Identity
    FRAMEWORK_IDENTITY = "EduAgent v1.0"

    def __init__(self, config: ApiConfig):
        self.config = config

        # Lifecycle manager for startup/shutdown events
        @asynccontextmanager
        async def lifespan(app: FastAPI):
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

    def run(self):
        """
        Starts the Uvicorn server.
        """
        uvicorn.run(self.app, host="0.0.0.0", port=self.config.port)

if __name__ == "__main__":
    config = ApiConfig(name="Edu API", port=8000)
    api = Api(config)
    api.run()