"""Processor for chat title generation tasks."""

from datetime import datetime

from edu_core.db.models import Chat
from edu_queue.schemas import ChatTitleGenerationData
from rich.console import Console

from processors.base import BaseProcessor
from processors.llm import create_llm_non_streaming

console = Console(force_terminal=True)


class ChatTitleProcessor(BaseProcessor[ChatTitleGenerationData]):
    """Processor for generating chat titles."""

    def __init__(
        self,
        azure_openai_chat_deployment: str,
        azure_openai_endpoint: str,
        azure_openai_api_version: str,
    ):
        """Initialize the processor.

        Args:
            azure_openai_chat_deployment: Azure OpenAI chat deployment name
            azure_openai_endpoint: Azure OpenAI endpoint URL
            azure_openai_api_version: Azure OpenAI API version
        """
        self.azure_openai_chat_deployment = azure_openai_chat_deployment
        self.azure_openai_endpoint = azure_openai_endpoint
        self.azure_openai_api_version = azure_openai_api_version

    async def process(self, payload: ChatTitleGenerationData) -> None:
        """Generate and update chat title.

        Args:
            payload: Chat title generation data
        """
        # Initialize LLM for title generation
        llm = create_llm_non_streaming(
            self.azure_openai_chat_deployment,
            self.azure_openai_endpoint,
            self.azure_openai_api_version,
            temperature=0.25,
        )

        # Generate title
        try:
            prompt = f"""Generate a concise, descriptive title (max 5 words) for a chat based on this conversation:

User: "{payload["user_message"]}"
Assistant: "{payload["ai_response"]}"

Only respond with the title, nothing else. Do not use quotes."""

            response = await llm.ainvoke(prompt)
            title = response.content.strip()

            # Remove quotes if present
            title = title.strip('"').strip("'")

            # Truncate if too long
            if len(title) > 60:
                title = title[:57] + "..."
        except Exception as e:
            console.print(
                f"[yellow]Error generating title, using default: {e}[/yellow]"
            )
            title = "New Chat"

        # Update chat in database
        with self._get_db_session() as db:
            chat = (
                db.query(Chat)
                .filter(
                    Chat.id == payload["chat_id"],
                    Chat.user_id == payload["user_id"],
                )
                .first()
            )
            if chat:
                chat.title = title
                chat.updated_at = datetime.now()
                # Commit is handled by _get_db_session context manager
                console.log(f"Generated title for chat {payload['chat_id']}: {title}")
            else:
                console.print(f"[yellow]Chat {payload['chat_id']} not found[/yellow]")
