"""Processor registry for mapping task types to processors."""

from edu_core.services.search import SearchService
from edu_queue.schemas import TaskType

from processors.base import BaseProcessor
from processors.chat_title import ChatTitleProcessor
from processors.document import DocumentProcessor
from processors.flashcard import FlashcardProcessor
from processors.mind_map import MindMapProcessor
from processors.note import NoteProcessor
from processors.quiz import QuizProcessor


class ProcessorRegistry:
    """Registry for task type to processor mapping."""

    def __init__(
        self,
        search_service: SearchService,
        azure_openai_chat_deployment: str,
        azure_openai_endpoint: str,
        azure_openai_api_version: str,
        azure_storage_connection_string: str,
        azure_storage_input_container_name: str,
        azure_storage_output_container_name: str,
        azure_cu_endpoint: str,
        azure_cu_key: str,
        azure_cu_analyzer_id: str,
        azure_openai_embedding_deployment: str,
    ):
        """Initialize the registry with required services.

        Args:
            search_service: SearchService for RAG
            azure_openai_chat_deployment: Azure OpenAI chat deployment name
            azure_openai_endpoint: Azure OpenAI endpoint URL
            azure_openai_api_version: Azure OpenAI API version
            azure_storage_connection_string: Azure Storage connection string
            azure_storage_input_container_name: Input container name
            azure_storage_output_container_name: Output container name
            azure_cu_endpoint: Azure Content Understanding endpoint
            azure_cu_key: Azure Content Understanding subscription key
            azure_cu_analyzer_id: Azure Content Understanding analyzer ID
            azure_openai_embedding_deployment: Azure OpenAI embedding deployment
        """
        self.search_service = search_service
        self.azure_openai_chat_deployment = azure_openai_chat_deployment
        self.azure_openai_endpoint = azure_openai_endpoint
        self.azure_openai_api_version = azure_openai_api_version
        self.azure_storage_connection_string = azure_storage_connection_string
        self.azure_storage_input_container_name = azure_storage_input_container_name
        self.azure_storage_output_container_name = azure_storage_output_container_name
        self.azure_cu_endpoint = azure_cu_endpoint
        self.azure_cu_key = azure_cu_key
        self.azure_cu_analyzer_id = azure_cu_analyzer_id
        self.azure_openai_embedding_deployment = azure_openai_embedding_deployment

    def get_processor(self, task_type: TaskType) -> BaseProcessor:
        """Get processor for a task type.

        Args:
            task_type: The task type

        Returns:
            Processor instance for the task type

        Raises:
            ValueError: If task type is unknown
        """
        processors = {
            TaskType.CHAT_TITLE_GENERATION: ChatTitleProcessor(
                self.azure_openai_chat_deployment,
                self.azure_openai_endpoint,
                self.azure_openai_api_version,
            ),
            TaskType.FLASHCARD_GENERATION: FlashcardProcessor(
                self.search_service,
                self.azure_openai_chat_deployment,
                self.azure_openai_endpoint,
                self.azure_openai_api_version,
                self.azure_storage_connection_string,
                self.azure_storage_output_container_name,
            ),
            TaskType.QUIZ_GENERATION: QuizProcessor(
                self.search_service,
                self.azure_openai_chat_deployment,
                self.azure_openai_endpoint,
                self.azure_openai_api_version,
                self.azure_storage_connection_string,
                self.azure_storage_output_container_name,
            ),
            TaskType.NOTE_GENERATION: NoteProcessor(
                self.search_service,
                self.azure_openai_chat_deployment,
                self.azure_openai_endpoint,
                self.azure_openai_api_version,
                self.azure_storage_connection_string,
                self.azure_storage_output_container_name,
            ),
            TaskType.MIND_MAP_GENERATION: MindMapProcessor(
                self.search_service,
                self.azure_openai_chat_deployment,
                self.azure_openai_endpoint,
                self.azure_openai_api_version,
                self.azure_storage_connection_string,
                self.azure_storage_output_container_name,
            ),
            TaskType.DOCUMENT_PROCESSING: DocumentProcessor(
                azure_storage_connection_string=self.azure_storage_connection_string,
                azure_storage_input_container_name=self.azure_storage_input_container_name,
                azure_storage_output_container_name=self.azure_storage_output_container_name,
                azure_cu_endpoint=self.azure_cu_endpoint,
                azure_cu_key=self.azure_cu_key,
                azure_cu_analyzer_id=self.azure_cu_analyzer_id,
                azure_openai_embedding_deployment=self.azure_openai_embedding_deployment,
                azure_openai_endpoint=self.azure_openai_endpoint,
                azure_openai_api_version=self.azure_openai_api_version,
            ),
        }

        processor = processors.get(task_type)
        if not processor:
            raise ValueError(f"Unknown task type: {task_type}")

        return processor
