"""FastAPI dependencies for service construction."""

from fastapi import Depends

from config import Settings, get_settings
from edu_shared.services import (
    ChatService,
    DocumentService,
    DocumentProcessingService,
    FlashcardGroupService,
    MindMapService,
    NoteService,
    PracticeService,
    ProjectService,
    QuizService,
    SearchService,
    StudySessionService,
    UserService,
)
from edu_shared.agents.base import ContentAgentConfig
from services.queue import QueueService


def get_settings_dep() -> Settings:
    """Get application settings."""
    return get_settings()


def get_project_service() -> ProjectService:
    """Get ProjectService instance."""
    return ProjectService()


def get_document_service() -> DocumentService:
    """Get DocumentService instance."""
    return DocumentService()


def get_chat_service(
    settings: Settings = Depends(get_settings_dep),
) -> ChatService:
    """Get ChatService instance."""
    return ChatService(
        azure_openai_chat_deployment=settings.azure_openai_chat_deployment,
        azure_openai_endpoint=settings.azure_openai_endpoint,
        azure_openai_api_version=settings.azure_openai_api_version,
    )


def get_note_service() -> NoteService:
    """Get NoteService instance."""
    return NoteService()


def get_quiz_service() -> QuizService:
    """Get QuizService instance."""
    return QuizService()


def get_flashcard_group_service() -> FlashcardGroupService:
    """Get FlashcardGroupService instance."""
    return FlashcardGroupService()


def get_user_service() -> UserService:
    """Get UserService instance."""
    return UserService()


def get_practice_service() -> PracticeService:
    """Get PracticeService instance."""
    return PracticeService()


def get_mind_map_service() -> MindMapService:
    """Get MindMapService instance."""
    return MindMapService()


def get_study_session_service() -> StudySessionService:
    """Get StudySessionService instance."""
    return StudySessionService()


def get_search_service(
    settings: Settings = Depends(get_settings_dep),
) -> SearchService:
    """Get SearchService instance with configuration from settings."""
    return SearchService(
        database_url=settings.database_url,
        azure_openai_embedding_deployment=settings.azure_openai_embedding_deployment,
        azure_openai_endpoint=settings.azure_openai_endpoint,
        azure_openai_api_version=settings.azure_openai_api_version,
    )


def get_content_agent_config(
    settings: Settings = Depends(get_settings_dep),
) -> ContentAgentConfig:
    """Get ContentAgentConfig instance with configuration from settings."""
    return ContentAgentConfig(
        azure_openai_chat_deployment=settings.azure_openai_chat_deployment,
        azure_openai_endpoint=settings.azure_openai_endpoint,
        azure_openai_api_version=settings.azure_openai_api_version,
    )


def get_chat_service_with_streaming(
    search_service: SearchService = Depends(get_search_service),
    settings: Settings = Depends(get_settings_dep),
) -> ChatService:
    """Get ChatService instance configured for streaming with SearchService."""
    return ChatService(
        search_service=search_service,
        azure_openai_chat_deployment=settings.azure_openai_chat_deployment,
        azure_openai_endpoint=settings.azure_openai_endpoint,
        azure_openai_api_version=settings.azure_openai_api_version,
    )


def get_document_processing_service(
    settings: Settings = Depends(get_settings_dep),
) -> DocumentProcessingService:
    """Get DocumentProcessingService instance with configuration from settings."""
    return DocumentProcessingService(
        database_url=settings.database_url,
        azure_storage_connection_string=settings.azure_storage_connection_string,
        azure_storage_input_container_name=settings.azure_storage_input_container_name,
        azure_storage_output_container_name=settings.azure_storage_output_container_name,
        azure_cu_endpoint="",
        azure_cu_key="",
        azure_cu_analyzer_id="",
        azure_openai_embedding_deployment="",  # Not used in upload
        azure_openai_endpoint="",  # Not used in upload
        azure_openai_api_version="",  # Not used in upload
    )


def get_queue_service(
    settings: Settings = Depends(get_settings_dep),
) -> QueueService:
    """Get QueueService instance with configuration from settings."""
    return QueueService(
        connection_string=settings.azure_storage_connection_string,
        queue_name=settings.azure_storage_queue_name,
    )

