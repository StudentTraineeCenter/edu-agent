"""Processor for quiz generation tasks."""

from edu_shared.agents.quiz_agent import QuizAgent
from edu_shared.schemas.queue import QuizGenerationData
from processors.llm import create_llm_non_streaming
from processors.base import BaseProcessor
from rich.console import Console

console = Console(force_terminal=True)


class QuizProcessor(BaseProcessor[QuizGenerationData]):
    """Processor for generating quizzes."""

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

    async def process(self, payload: QuizGenerationData) -> None:
        """Generate quiz questions using AI and populate the quiz.
        
        Args:
            payload: Quiz generation data
            
        Raises:
            NotFoundError: If quiz or project not found
        """
        # Generate quiz using AI
        llm = create_llm_non_streaming(
            self.azure_openai_chat_deployment,
            self.azure_openai_endpoint,
            self.azure_openai_api_version,
        )
        
        quiz_agent = QuizAgent(
            search_service=self.search_service,
            llm=llm,
        )
        
        await quiz_agent.generate_and_save(
            project_id=payload["project_id"],
            topic=payload.get("topic"),
            custom_instructions=payload.get("custom_instructions"),
            quiz_id=payload["quiz_id"],
            count=payload.get("count"),
        )

        console.log(f"Populated quiz {payload['quiz_id']}")
