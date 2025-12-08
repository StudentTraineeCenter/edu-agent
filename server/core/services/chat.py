"""Service for managing chats with AI-powered responses."""

import asyncio
from contextlib import contextmanager
from datetime import datetime
from typing import AsyncGenerator, List, Optional
from uuid import uuid4

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from langchain_core.messages import AIMessage, BaseMessage, ToolCall
from langchain_openai import AzureChatOpenAI
from pydantic import BaseModel

from core.agents.context import CustomAgentContext
from core.agents.factory import make_agent
from core.agents.search import SearchInterface
from core.config import app_config
from core.logger import get_logger
from core.services.flashcards import FlashcardService
from core.services.quizzes import QuizService
from core.services.usage import UsageService
from db.models import Chat, ChatMessage, ChatMessageSource, ChatMessageToolCall
from db.session import SessionLocal

logger = get_logger(__name__)


class MessageChunk(BaseModel):
    """Model for streaming message chunks."""

    chunk: str
    done: bool
    status: Optional[str] = None  # Status message: thinking, searching, generating
    sources: List[ChatMessageSource] = []
    tools: List[ChatMessageToolCall] = []
    id: Optional[str] = None
    response: Optional[str] = None  # Full response at the end


class ChatService:
    """Service for managing chats with AI-powered responses."""

    def __init__(
        self, search_interface: SearchInterface, usage_service: UsageService = None
    ) -> None:
        """Initialize the chat service.

        Args:
            search_interface: Search interface for document retrieval
            usage_service: Optional usage tracking service
        """
        self.search_interface = search_interface
        self.usage_service = usage_service
        self.flashcard_service = FlashcardService(search_interface=search_interface)
        self.quiz_service = QuizService(search_interface=search_interface)
        self.credential = DefaultAzureCredential()

        self.token_provider = get_bearer_token_provider(
            self.credential, "https://cognitiveservices.azure.com/.default"
        )

        self.llm_streaming = AzureChatOpenAI(
            azure_deployment=app_config.AZURE_OPENAI_CHAT_DEPLOYMENT,
            azure_endpoint=app_config.AZURE_OPENAI_ENDPOINT,
            api_version="2024-12-01-preview",
            azure_ad_token_provider=self.token_provider,
            temperature=0,
            streaming=True,
        )

        self.llm_non_streaming = AzureChatOpenAI(
            azure_deployment=app_config.AZURE_OPENAI_CHAT_DEPLOYMENT,
            azure_endpoint=app_config.AZURE_OPENAI_ENDPOINT,
            api_version="2024-12-01-preview",
            azure_ad_token_provider=self.token_provider,
            temperature=0,
            streaming=False,
        )

    def create_chat(self, project_id: str, user_id: str, title: Optional[str]) -> Chat:
        """Create a new chat.

        Args:
            project_id: The project ID
            user_id: The user's ID
            title: Optional chat title

        Returns:
            Created Chat model instance
        """
        with self._get_db_session() as db:
            try:
                chat = Chat(
                    id=str(uuid4()),
                    project_id=project_id,
                    user_id=user_id,
                    title=title,
                    messages=[],
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )
                if not title:
                    chat.title = f"Chat {chat.id[:8]}"
                db.add(chat)
                db.commit()
                db.refresh(chat)
                logger.info(f"created chat chat_id={chat.id}")
                return chat
            except Exception as e:
                logger.error(f"error creating chat for project_id={project_id}: {e}")
                raise

    def get_chat(self, chat_id: str, user_id: str) -> Optional[Chat]:
        """Get a chat by ID.

        Args:
            chat_id: The chat ID
            user_id: The user's ID

        Returns:
            Chat model instance or None if not found
        """
        with self._get_db_session() as db:
            try:
                chat = (
                    db.query(Chat)
                    .filter(Chat.id == chat_id, Chat.user_id == user_id)
                    .first()
                )
                if chat:
                    logger.info(f"retrieved chat chat_id={chat_id}")
                return chat
            except Exception as e:
                logger.error(f"error getting chat chat_id={chat_id}: {e}")
                raise

    def list_chats(self, project_id: str, user_id: str) -> List[Chat]:
        """List all chats for a project.

        Args:
            project_id: The project ID
            user_id: The user's ID

        Returns:
            List of Chat model instances
        """
        with self._get_db_session() as db:
            try:
                chats = (
                    db.query(Chat)
                    .filter(
                        Chat.project_id == project_id,
                        Chat.user_id == user_id,
                    )
                    .order_by(Chat.created_at.desc())
                    .all()
                )
                logger.info(f"listed {len(chats)} chats for project_id={project_id}")
                return chats
            except Exception as e:
                logger.error(f"error listing chats for project_id={project_id}: {e}")
                raise

    def update_chat(self, chat_id: str, user_id: str, title: Optional[str]) -> Chat:
        """Update a chat.

        Args:
            chat_id: The chat ID
            user_id: The user's ID
            title: Optional new title

        Returns:
            Updated Chat model instance

        Raises:
            ValueError: If chat not found
        """
        with self._get_db_session() as db:
            try:
                chat = (
                    db.query(Chat)
                    .filter(Chat.id == chat_id, Chat.user_id == user_id)
                    .first()
                )
                if not chat:
                    raise ValueError(f"Chat {chat_id} not found")

                chat.title = title
                db.commit()
                db.refresh(chat)

                logger.info(f"updated chat chat_id={chat_id}")
                return chat
            except ValueError:
                raise
            except Exception as e:
                logger.error(f"error updating chat chat_id={chat_id}: {e}")
                raise

    def delete_chat(self, chat_id: str, user_id: str) -> None:
        """Delete a chat.

        Args:
            chat_id: The chat ID
            user_id: The user's ID

        Raises:
            ValueError: If chat not found
        """
        with self._get_db_session() as db:
            try:
                chat = (
                    db.query(Chat)
                    .filter(Chat.id == chat_id, Chat.user_id == user_id)
                    .first()
                )
                if not chat:
                    raise ValueError(f"Chat {chat_id} not found")

                db.delete(chat)
                db.commit()

                logger.info(f"deleted chat chat_id={chat_id}")
            except ValueError:
                raise
            except Exception as e:
                logger.error(f"error deleting chat chat_id={chat_id}: {e}")
                raise

    async def send_streaming_message(
        self, chat_id: str, user_id: str, message: str
    ) -> AsyncGenerator[MessageChunk, None]:
        """Send a streaming message to a chat using grounded RAG responses.

        Args:
            chat_id: The chat ID
            user_id: The user's ID
            message: The message to send

        Yields:
            MessageChunk instances containing message chunks and metadata
        """
        with self._get_db_session() as db:
            try:
                chat = (
                    db.query(Chat)
                    .filter(Chat.id == chat_id, Chat.user_id == user_id)
                    .first()
                )
                if not chat:
                    raise ValueError(f"Chat {chat_id} not found")

                messages = [ChatMessage(**msg) for msg in chat.messages]
                assistant_message_id = str(uuid4())
                is_first_message = len(messages) == 0

                # Stream the response
                async for chunk_data in self._get_response_stream(
                    query=message,
                    messages=messages,
                    language_code=chat.project.language_code,
                    project_id=chat.project_id,
                    user_id=user_id,
                ):
                    # If this is the final chunk, save the complete message to database
                    if chunk_data.done and (chunk_data.response is not None):
                        sources_data = [
                            source.model_dump() for source in chunk_data.sources or []
                        ]
                        tools_data = [
                            tool.model_dump() for tool in chunk_data.tools or []
                        ]

                        chat.messages = chat.messages + [
                            {
                                "role": "user",
                                "content": message,
                                "id": str(uuid4()),
                                "created_at": datetime.now().isoformat(),
                            },
                            {
                                "id": assistant_message_id,
                                "role": "assistant",
                                "content": chunk_data.response,
                                "sources": sources_data,
                                "tools": tools_data,
                                "created_at": datetime.now().isoformat(),
                            },
                        ]

                        # Generate title for first message
                        if is_first_message:
                            generated_title = await self._generate_chat_title(
                                message, chunk_data.response
                            )
                            chat.title = generated_title
                            logger.info(f"generated chat title: {generated_title}")

                        chat.updated_at = datetime.now()
                        db.commit()

                        # Yield final chunk
                        chunk_data.id = assistant_message_id
                        chunk_data.chunk = ""  # Avoid duplication

                    # Stream chunk with message_id
                    chunk_data.id = assistant_message_id
                    yield chunk_data
            except Exception as e:
                logger.error(
                    f"error sending streaming message to chat_id={chat_id}: {e}"
                )
                yield MessageChunk(
                    chunk=f"Error: {str(e)}",
                    done=True,
                    sources=[],
                    tools=[],
                    id="",
                )

    async def _get_response_stream(
        self,
        query: str,
        messages: list[ChatMessage],
        project_id: str,
        language_code: str,
        user_id: str = None,
    ):
        """Get response stream from agent.

        Args:
            query: The user's query
            messages: List of previous chat messages
            project_id: The project ID
            language_code: Language code for responses
            user_id: Optional user ID

        Yields:
            MessageChunk instances containing response chunks and metadata
        """
        # --- helpers ------------------------------------------------------------
        chat_history = [{"role": m.role, "content": m.content} for m in messages[-10:]]

        async def yield_tool_update():
            yield MessageChunk(chunk="", done=False, tools=list(tool_calls.values()))
            await asyncio.sleep(0.001)

        # --- agent + state ------------------------------------------------------
        agent = make_agent()

        buffer_parts: list[str] = []
        gathered_sources: list[ChatMessageSource] = []
        tool_calls: dict[str, ChatMessageToolCall] = {}
        has_started_generating = False

        chat_history.append({"role": "user", "content": query})

        ctx = CustomAgentContext(
            project_id=project_id,
            user_id=user_id,
            usage=self.usage_service,
            search=self.search_interface,
            language=language_code,
        )

        # Send initial "thinking" status
        yield MessageChunk(chunk="", done=False, status="thinking")
        await asyncio.sleep(0.001)

        # --- process stream chunks ----------------------------------------------
        async for chunk in agent.astream(
            {"messages": chat_history, "sources": []},
            stream_mode="updates",
            context=ctx,
        ):
            # Extract sources from middleware hooks
            chunk_key = (
                "ensure_sources_in_stream.after_model"
                if "ensure_sources_in_stream.after_model" in chunk
                else "fetch_and_set_sources.before_model"
            )
            if chunk_key in chunk:
                middleware_data = chunk.get(chunk_key) or {}
                model_sources: list[ChatMessageSource] = middleware_data.get(
                    "sources", []
                )

                # Send "searching" status when RAG is fetching documents
                if chunk_key == "fetch_and_set_sources.before_model" and model_sources:
                    yield MessageChunk(chunk="", done=False, status="searching")
                    await asyncio.sleep(0.001)

                for source in model_sources:
                    if not any(s.id == source.id for s in gathered_sources):
                        gathered_sources.append(source)

            # Handle model chunks (AI responses)
            if "model" in chunk:
                # Send "generating" status when first content arrives
                if not has_started_generating:
                    yield MessageChunk(chunk="", done=False, status="generating")
                    await asyncio.sleep(0.001)
                    has_started_generating = True

                msgs: list[BaseMessage] = chunk["model"].get("messages", [])
                for msg in msgs:
                    # Extract content if available
                    if msg.content:
                        buffer_parts.append(msg.content)
                        yield MessageChunk(chunk=msg.content, done=False)
                        await asyncio.sleep(0.001)

                    # Extract tool calls from AIMessage
                    if isinstance(msg, AIMessage):
                        tool_calls_list: list[ToolCall] = msg.tool_calls or []
                        for tc in tool_calls_list:
                            tc_id = tc.get("id") or str(uuid4())
                            tc_name = tc.get("name") or ""
                            tc_args = tc.get("args") or {}

                            # Create or update tool call entry
                            if tc_id not in tool_calls:
                                tool_calls[tc_id] = ChatMessageToolCall(
                                    id=tc_id,
                                    type=f"tool-call-{tc_name}",
                                    name=tc_name,
                                    state="input-available",
                                    input=tc_args,
                                    output=None,
                                    error_text=None,
                                )
                            elif not tool_calls[tc_id].input:
                                tool_calls[tc_id].input = tc_args

                            async for update_chunk in yield_tool_update():
                                yield update_chunk

        # --- finalize -----------------------------------------------------------
        final_text = "".join(buffer_parts)

        yield MessageChunk(
            chunk="",
            done=True,
            sources=gathered_sources,
            tools=list(tool_calls.values()),
            response=final_text,
        )

    async def _generate_chat_title(self, user_message: str, ai_response: str) -> str:
        """Generate a concise chat title based on the first exchange.

        Args:
            user_message: The user's first message
            ai_response: The AI's first response

        Returns:
            Generated chat title
        """
        try:
            prompt = f"""Generate a concise, descriptive title (max 5 words) for a chat based on this conversation:

User: "{user_message}"
Assistant: "{ai_response}"

Only respond with the title, nothing else. Do not use quotes."""

            response = await self.llm_non_streaming.ainvoke(prompt)
            title = response.content.strip()

            # Remove quotes if present
            title = title.strip('"').strip("'")

            # Truncate if too long
            if len(title) > 60:
                title = title[:57] + "..."

            return title
        except Exception as e:
            logger.error(f"error generating chat title: {e}")
            return "New Chat"

    @contextmanager
    def _get_db_session(self):
        """Context manager for database sessions."""
        db = SessionLocal()
        try:
            yield db
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
