"""FastAPI dependencies for service construction."""

from config import Settings, get_settings
from edu_core.services import (
    ChatService,
    DocumentService,
    DocumentUploadService,
    FlashcardGroupService,
    MindMapService,
    NoteService,
    PracticeService,
    ProjectService,
    QuizService,
    SearchService,
    StudySessionService,
    UsageService,
    UserService,
)
from edu_queue.service import QueueService
from fastapi import Depends


def get_settings_dep() -> Settings:
    """Get application settings."""
    return get_settings()


def get_queue_service(
    settings: Settings = Depends(get_settings_dep),
) -> QueueService:
    """Get QueueService instance with configuration from settings."""
    return QueueService(
        connection_string=settings.azure_storage_connection_string,
        queue_name=settings.azure_storage_queue_name,
    )


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


def get_usage_service(
    settings: Settings = Depends(get_settings_dep),
) -> UsageService:
    """Get UsageService instance with configuration from settings."""
    return UsageService(
        max_chat_messages_per_day=settings.max_chat_messages_per_day,
        max_flashcard_generations_per_day=settings.max_flashcard_generations_per_day,
        max_quiz_generations_per_day=settings.max_quiz_generations_per_day,
        max_document_uploads_per_day=settings.max_document_uploads_per_day,
    )


def get_project_service() -> ProjectService:
    """Get ProjectService instance."""
    return ProjectService()


def get_document_service() -> DocumentService:
    """Get DocumentService instance."""
    return DocumentService()


def get_chat_service(
    settings: Settings = Depends(get_settings_dep),
    usage_service: UsageService = Depends(get_usage_service),
    queue_service: QueueService = Depends(get_queue_service),
    search_service: SearchService = Depends(get_search_service),
) -> ChatService:
    """Get ChatService instance."""
    return ChatService(
        search_service=search_service,
        azure_openai_chat_deployment=settings.azure_openai_chat_deployment,
        azure_openai_endpoint=settings.azure_openai_endpoint,
        azure_openai_api_version=settings.azure_openai_api_version,
        usage_service=usage_service,
        queue_service=queue_service,
    )


def get_note_service(
    queue_service: QueueService = Depends(get_queue_service),
) -> NoteService:
    """Get NoteService instance."""
    return NoteService(queue_service=queue_service)


def get_quiz_service(
    queue_service: QueueService = Depends(get_queue_service),
) -> QuizService:
    """Get QuizService instance."""
    return QuizService(queue_service=queue_service)


def get_flashcard_group_service(
    queue_service: QueueService = Depends(get_queue_service),
) -> FlashcardGroupService:
    """Get FlashcardGroupService instance."""
    return FlashcardGroupService(queue_service=queue_service)


def get_user_service() -> UserService:
    """Get UserService instance."""
    return UserService()


def get_practice_service() -> PracticeService:
    """Get PracticeService instance."""
    return PracticeService()


def get_mind_map_service(
    queue_service: QueueService = Depends(get_queue_service),
) -> MindMapService:
    """Get MindMapService instance."""
    return MindMapService(queue_service=queue_service)


def get_study_session_service() -> StudySessionService:
    """Get StudySessionService instance."""
    return StudySessionService()


def get_chat_service_with_streaming(
    search_service: SearchService = Depends(get_search_service),
    settings: Settings = Depends(get_settings_dep),
    usage_service: UsageService = Depends(get_usage_service),
    queue_service: QueueService = Depends(get_queue_service),
) -> ChatService:
    """Get ChatService instance configured for streaming with SearchService."""
    return ChatService(
        search_service=search_service,
        azure_openai_chat_deployment=settings.azure_openai_chat_deployment,
        azure_openai_endpoint=settings.azure_openai_endpoint,
        azure_openai_api_version=settings.azure_openai_api_version,
        usage_service=usage_service,
        queue_service=queue_service,
    )


def get_document_upload_service(
    settings: Settings = Depends(get_settings_dep),
) -> DocumentUploadService:
    """Get DocumentUploadService instance with configuration from settings."""
    return DocumentUploadService(
        database_url=settings.database_url,
        azure_storage_connection_string=settings.azure_storage_connection_string,
        azure_storage_input_container_name=settings.azure_storage_input_container_name,
    )
