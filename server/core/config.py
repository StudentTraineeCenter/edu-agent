import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class AppConfig:
    # DATABASE
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:postgres@localhost:5432/postgres",
    )

    # BLOB
    AZURE_STORAGE_CONNECTION_STRING: str = (
        os.getenv("AZURE_STORAGE_CONNECTION_STRING") or "missing_env_var"
    )
    AZURE_STORAGE_CONTAINER_NAME: str = (
        os.getenv("AZURE_STORAGE_CONTAINER_NAME") or "missing_env_var"
    )

    # OPENAI
    AZURE_OPENAI_API_KEY: str = os.getenv("AZURE_OPENAI_API_KEY") or "missing_env_var"
    AZURE_OPENAI_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT") or "missing_env_var"
    AZURE_OPENAI_DEFAULT_MODEL: str = os.getenv("AZURE_OPENAI_DEFAULT_MODEL", "gpt-4o")
    AZURE_OPENAI_EMBEDDING_MODEL: str = os.getenv(
        "AZURE_OPENAI_EMBEDDING_MODEL", "text-embedding-3-large"
    )
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT: str = os.getenv(
        "AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-large"
    )
    AZURE_OPENAI_CHAT_DEPLOYMENT: str = os.getenv(
        "AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4o"
    )
    AZURE_OPENAI_API_VERSION: str = os.getenv("AZURE_OPENAI_API_VERSION", "2024-06-01")

    # AZURE AI DOCUMENT INTELLIGENCE
    AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT: str = (
        os.getenv("AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT") or "missing_env_var"
    )
    AZURE_DOCUMENT_INTELLIGENCE_KEY: str = (
        os.getenv("AZURE_DOCUMENT_INTELLIGENCE_KEY") or "missing_env_var"
    )


app_config = AppConfig()
