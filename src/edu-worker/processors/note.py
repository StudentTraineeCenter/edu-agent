"""Processor for note generation tasks."""

from azure.storage.blob import BlobServiceClient
from edu_ai.agents.note_agent import NoteAgent
from edu_ai.agents.topic_graph_agent import TopicGraphAgent
from edu_queue.schemas import NoteGenerationData
from rich.console import Console

from processors.base import BaseProcessor
from processors.llm import create_llm_non_streaming

console = Console(force_terminal=True)


class NoteProcessor(BaseProcessor[NoteGenerationData]):
    """Processor for generating notes."""

    def __init__(
        self,
        search_service,
        azure_openai_chat_deployment: str,
        azure_openai_endpoint: str,
        azure_openai_api_version: str,
        azure_storage_connection_string: str,
        azure_storage_output_container_name: str,
    ):
        """Initialize the processor.

        Args:
            search_service: SearchService for RAG
            azure_openai_chat_deployment: Azure OpenAI chat deployment name
            azure_openai_endpoint: Azure OpenAI endpoint URL
            azure_openai_api_version: Azure OpenAI API version
            azure_storage_connection_string: Azure Storage connection string
            azure_storage_output_container_name: Output container name
        """
        self.search_service = search_service
        self.azure_openai_chat_deployment = azure_openai_chat_deployment
        self.azure_openai_endpoint = azure_openai_endpoint
        self.azure_openai_api_version = azure_openai_api_version
        self.azure_storage_connection_string = azure_storage_connection_string
        self.azure_storage_output_container_name = azure_storage_output_container_name

    async def process(self, payload: NoteGenerationData) -> None:
        """Generate note content using AI and populate the note.

        Args:
            payload: Note generation data

        Raises:
            NotFoundError: If note or project not found
        """
        # Generate note using AI
        llm = create_llm_non_streaming(
            self.azure_openai_chat_deployment,
            self.azure_openai_endpoint,
            self.azure_openai_api_version,
        )

        blob_service_client = BlobServiceClient.from_connection_string(
            self.azure_storage_connection_string
        )

        topic_graph_agent = TopicGraphAgent(
            search_service=self.search_service,
            llm=llm,
            blob_service_client=blob_service_client,
            output_container=self.azure_storage_output_container_name,
        )

        note_agent = NoteAgent(
            search_service=self.search_service,
            llm=llm,
            topic_graph_agent=topic_graph_agent,
        )

        await note_agent.generate_and_save(
            project_id=payload["project_id"],
            topic=payload.get("topic"),
            custom_instructions=payload.get("custom_instructions"),
            note_id=payload["note_id"],
        )

        console.log(f"Populated note {payload['note_id']}")
