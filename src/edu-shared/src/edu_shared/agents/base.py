import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, TypeVar, Generic, Optional, Type, Any

from langchain_openai import AzureChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

from edu_shared.agents.prompts_utils import render_prompt

if TYPE_CHECKING:
    from edu_shared.services.search import SearchService

logger = logging.getLogger(__name__)

# Generic Output Type (e.g., FlashcardResult, QuizResult)
T = TypeVar("T", bound=BaseModel)

class ContentAgentConfig(BaseModel):
    azure_openai_chat_deployment: str
    azure_openai_endpoint: str
    azure_openai_api_version: str

class BaseContentAgent(ABC, Generic[T]):
    """
    Base Agent for AI generation.
    Directly uses DocumentService for RAG and AzureChatOpenAI for generation.
    """

    def __init__(self, config: ContentAgentConfig, search_service: "SearchService"):
        self.search_service = search_service
        self.config = config
        
        # Initialize Azure OpenAI once for all agents
        token_provider = get_bearer_token_provider(
            DefaultAzureCredential(), 
            "https://cognitiveservices.azure.com/.default"
        )
        
        self.llm = AzureChatOpenAI(
            azure_deployment=self.config.azure_openai_chat_deployment,
            azure_endpoint=self.config.azure_openai_endpoint,
            api_version=self.config.azure_openai_api_version,
            azure_ad_token_provider=token_provider,
            temperature=0.7,
        )

    @property
    @abstractmethod
    def output_model(self) -> Type[T]:
        """Pydantic model class for the output structure."""
        pass

    @property
    @abstractmethod
    def prompt_template(self) -> str:
        """Filename of the Jinja2 prompt template."""
        pass

    async def generate(
        self, 
        project_id: str, 
        topic: str, 
        custom_instructions: Optional[str] = None,
        **kwargs: Any
    ) -> T:
        """
        Main generation flow:
        1. Search documents using 'topic'
        2. Build Prompt (Context + Instructions)
        3. Call LLM
        4. Parse Result
        """
        logger.info(f"[{self.__class__.__name__}] Generating for topic: {topic}")

        # 1. RAG Search
        context_text = await self._get_context(project_id, topic)
        
        # 2. Prepare Parser
        parser = JsonOutputParser(pydantic_object=self.output_model)
        
        # 3. Render Prompt
        prompt_input = render_prompt(
            self.prompt_template,
            document_content=context_text,
            topic=topic,
            custom_instructions=custom_instructions or "No specific instructions.",
            format_instructions=parser.get_format_instructions(),
            **kwargs  # Pass extra args like 'count', 'difficulty'
        )

        # 4. Invoke LLM
        try:
            response = await self.llm.ainvoke(prompt_input)
            parsed_data = parser.parse(response.content)
            return self.output_model(**parsed_data)
        except Exception as e:
            logger.error(f"AI Generation failed: {e}")
            raise

    async def _get_context(self, project_id: str, topic: str) -> str:
        """Fetch relevant document segments directly from DocumentService."""
        if not topic:
            logger.warning(f"No topic provided for project: {project_id}")
            return ""
            
        # Use existing search logic in DocumentService
        # We request top 10 chunks to give the AI enough context
        results = await self.search_service.search_documents(
            query=topic, 
            project_id=project_id, 
            top_k=10
        )
        
        if not results:
            logger.warning(f"No documents found for topic: {topic}")
            return "No relevant documents found in the project."

        # Join content blocks
        return "\n\n---\n\n".join([r.content for r in results]) 