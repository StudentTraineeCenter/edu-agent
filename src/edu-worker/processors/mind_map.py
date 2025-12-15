"""Processor for mind map generation tasks."""

from edu_shared.agents.mind_map_agent import MindMapAgent
from edu_shared.schemas.queue import MindMapGenerationData
from processors.llm import create_llm_non_streaming
from processors.base import BaseProcessor
from rich.console import Console

console = Console(force_terminal=True)


class MindMapProcessor(BaseProcessor[MindMapGenerationData]):
    """Processor for generating mind maps."""

    def __init__(
        self,
        search_service,
        azure_openai_chat_deployment: str,
        azure_openai_endpoint: str,
        azure_openai_api_version: str,
    ):
        """Initialize the processor.
        
        Args:
            search_service: SearchService for RAG
            azure_openai_chat_deployment: Azure OpenAI chat deployment name
            azure_openai_endpoint: Azure OpenAI endpoint URL
            azure_openai_api_version: Azure OpenAI API version
        """
        self.search_service = search_service
        self.azure_openai_chat_deployment = azure_openai_chat_deployment
        self.azure_openai_endpoint = azure_openai_endpoint
        self.azure_openai_api_version = azure_openai_api_version

    async def process(self, payload: MindMapGenerationData) -> None:
        """Generate mind map content using AI and populate the mind map.
        
        Args:
            payload: Mind map generation data
            
        Raises:
            NotFoundError: If mind_map_id is provided but mind map not found
        """
        # Generate mind map using AI
        llm = create_llm_non_streaming(
            self.azure_openai_chat_deployment,
            self.azure_openai_endpoint,
            self.azure_openai_api_version,
        )
        
        mind_map_agent = MindMapAgent(
            search_service=self.search_service,
            llm=llm,
        )
        
        mind_map = await mind_map_agent.generate_and_save(
            project_id=payload["project_id"],
            topic=payload.get("topic"),
            custom_instructions=payload.get("custom_instructions"),
            mind_map_id=payload.get("mind_map_id"),
            user_id=payload["user_id"],
        )
        mind_map_id = mind_map.id

        if payload.get("mind_map_id"):
            console.log(f"Populated mind map {mind_map_id}: {mind_map.title}")
        else:
            console.log(f"Generated new mind map {mind_map_id}: {mind_map.title}")
