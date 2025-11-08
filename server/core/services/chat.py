import asyncio
import json
import re
from contextlib import contextmanager
from datetime import datetime
from db.models import ChatMessageToolCall
from typing import Any, AsyncGenerator, Dict, List, Optional
from uuid import uuid4

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from core.agents.factory import make_agent
from core.agents.search import SearchInterface
from core.config import app_config
from core.logger import get_logger
from core.services.usage import UsageService
from db.models import Chat, ChatMessage, ChatMessageSource, ChatMessageToolCall
from db.session import SessionLocal
from langchain_openai import AzureChatOpenAI
from pydantic import BaseModel

logger = get_logger(__name__)


class MessageChunk(BaseModel):
    chunk: str
    done: bool
    sources: List[ChatMessageSource] = []
    tools: List[ChatMessageToolCall] = []
    id: Optional[str] = None
    response: Optional[str] = None  # Full response at the end


class ChatService:
    def __init__(self, search_interface: SearchInterface, usage_service: UsageService = None):
        self.search_interface = search_interface
        self.usage_service = usage_service or UsageService()
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
        """Create a new chat"""

        with self._get_db_session() as db:
            chat = Chat(
                id=str(uuid4()),
                project_id=project_id,
                user_id=user_id,
                title=title,
                messages=[],
                created_at=datetime.now(),
                updated_at=datetime.now(),
                archived_at=None,
            )
            if not title:
                chat.title = f"Chat {chat.id[:8]}"
            db.add(chat)
            db.commit()
            db.refresh(chat)
            logger.info("chat created chat_id=%s", chat.id)
            return chat

    def get_chat(self, chat_id: str, user_id: str) -> Optional[Chat]:
        """Get a chat by id"""
        with self._get_db_session() as db:
            try:
                chat = (
                    db.query(Chat)
                    .filter(Chat.id == chat_id, Chat.user_id == user_id)
                    .first()
                )
                return chat
            except Exception as e:
                logger.error("error getting chat: %s", e)
                raise e

    def list_chats(self, project_id: str, user_id: str) -> List[Chat]:
        """List all chats for a project"""
        with self._get_db_session() as db:
            try:
                return (
                    db.query(Chat)
                    .filter(Chat.project_id == project_id, Chat.user_id == user_id, Chat.archived_at.is_(None))
                    .all()
                )
            except Exception as e:
                logger.error("error listing chats: %s", e)
                raise e

    def update_chat(self, chat_id: str, user_id: str, title: Optional[str]) -> Chat:
        """Update a chat"""
        with self._get_db_session() as db:
            try:
                chat = (
                    db.query(Chat)
                    .filter(Chat.id == chat_id, Chat.user_id == user_id)
                    .first()
                )
                if not chat:
                    raise ValueError(f"Chat with id {chat_id} not found")

                chat.title = title

                db.commit()
                db.refresh(chat)
                return chat
            except Exception as e:
                logger.error("error updating chat: %s", e)
                raise e

    def archive_chat(self, chat_id: str, user_id: str) -> Chat:
        """Archive a chat"""
        with self._get_db_session() as db:
            try:
                chat: Optional[Chat] = (
                    db.query(Chat)
                    .filter(Chat.id == chat_id, Chat.user_id == user_id)
                    .first()
                )
                if not chat:
                    raise ValueError(f"Chat with id {chat_id} not found")

                chat.archived_at = datetime.now()

                db.commit()
                db.refresh(chat)
                return chat
            except Exception as e:
                logger.error("error archiving chat: %s", e)
                raise e

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

    async def _generate_chat_title(self, user_message: str, ai_response: str) -> str:
        """Generate a concise chat title based on the first exchange."""
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
            logger.error("error generating chat title: %s", e)
            return "New Chat"

    async def send_streaming_message(
        self, chat_id: str, user_id: str, message: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Send a streaming message to a chat using grounded RAG responses"""
        with self._get_db_session() as db:
            try:
                chat: Optional[Chat] = (
                    db.query(Chat)
                    .filter(Chat.id == chat_id, Chat.user_id == user_id)
                    .first()
                )
                if not chat:
                    raise ValueError(f"Chat with id {chat_id} not found")

                messages: list[ChatMessage] = [
                    ChatMessage(**msg) for msg in chat.messages
                ]
                assistant_message_id = str(uuid4())
                is_first_message = len(messages) == 0

                def to_dict_list(items: List[Any]) -> List[Dict[str, Any]]:
                    """Convert list of models/dicts to list of dicts."""
                    return [
                        item if isinstance(item, dict) else item.model_dump()
                        for item in items
                    ]

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
                        sources = to_dict_list(chunk_data.sources or [])
                        tools = to_dict_list(chunk_data.tools or [])

                        chat.messages = chat.messages + [
                            {"role": "user", "content": message, "id": str(uuid4()), "created_at": datetime.now().isoformat()},
                            {
                                "id": assistant_message_id,
                                "role": "assistant",
                                "content": chunk_data.response,
                                "sources": sources,
                                "tools": tools,
                                "created_at": datetime.now().isoformat(),
                            },
                        ]

                        # Generate title for first message
                        if is_first_message:
                            generated_title = await self._generate_chat_title(
                                message, chunk_data.response
                            )
                            chat.title = generated_title
                            logger.info("generated chat title: %s", generated_title)

                        chat.updated_at = datetime.now()
                        db.commit()

                        # Yield final chunk
                        chunk_data.id = assistant_message_id
                        chunk_data.chunk = ""  # Avoid duplication

                    # Stream chunk with message_id
                    yield {
                        **chunk_data.model_dump(),
                        "chat_id": chat_id,
                        "id": assistant_message_id,
                    }

            except Exception as e:
                logger.error("error sending streaming message: %s", e)
                yield MessageChunk(
                    chunk=f"Error: {str(e)}",
                    done=True,
                    sources=[],
                    tools=[],
                    id="",
                ).model_dump()

    async def _get_response_stream(
        self,
        query: str,
        messages: list[ChatMessage],
        project_id: str,
        language_code: str,
        user_id: str = None,
    ):
        # Convert your last 6 messages to history
        chat_history = []
        for m in messages[-6:]:
            chat_history.append({"role": m.role, "content": m.content})

        agent = make_agent(
            language_code=language_code,
            project_id=project_id,
            search_interface=self.search_interface,
            user_id=user_id,
            usage_service=self.usage_service,
        )
        user_input = query

        buffer_parts: list[str] = []
        gathered_sources: list[ChatMessageSource] = []
        tool_calls: dict[str, ChatMessageToolCall] = {}  # Track tool calls by run_id

        def fix_backticks(text: str) -> str:
            """Add newlines around triple backticks for proper markdown rendering."""
            if "```" not in text:
                return text
            text = re.sub(r"```(?!\n)", r"```\n", text)
            text = re.sub(r"(?<!\n)```", r"\n```", text)
            return text

        def serialize_output(val: Any):
            """Serialize tool output to JSON-compatible format."""
            if val is None:
                return None
            if hasattr(val, "model_dump"):
                return val.model_dump()
            if hasattr(val, "dict"):
                return val.dict()
            if isinstance(val, (dict, str)):
                return val
            return str(val)

        async def yield_tool_update(run_id: str):
            """Helper to yield tool call updates."""
            yield MessageChunk(chunk="", done=False, tools=list(tool_calls.values()))
            await asyncio.sleep(0.001)

        # Stream tokens to the client
        async for ev in agent.astream_events(
            {"input": user_input, "chat_history": chat_history}, version="v1"
        ):
            kind = ev["event"]

            if kind == "on_chat_model_stream":
                chunk_obj = ev.get("data", {}).get("chunk")
                tok = getattr(chunk_obj, "content", None)
                if tok:
                    buffer_parts.append(tok)
                    yield MessageChunk(chunk=fix_backticks(tok), done=False)
                    await asyncio.sleep(0.001)

            elif kind == "on_tool_start":
                run_id = ev.get("run_id", "")
                tool_input = ev.get("data", {}).get("input", {})
                tool_name = ev.get("name", "")

                tool_calls[run_id] = ChatMessageToolCall(
                    id=run_id,
                    type=f"tool-call-{tool_name}",
                    name=tool_name,
                    state="input-available",
                    input=tool_input if isinstance(tool_input, dict) else None,
                    output=None,
                    error_text=None,
                ).model_dump()

                print(tool_calls)

                async for chunk in yield_tool_update(run_id):
                    yield chunk

            elif kind == "on_tool_end":
                run_id = ev.get("run_id", "")
                out = ev.get("data", {}).get("output")

                if run_id in tool_calls:
                    tool_calls[run_id]["state"] = "output-available"
                    tool_calls[run_id]["output"] = serialize_output(out)

                    async for chunk in yield_tool_update(run_id):
                        yield chunk

                    # Extract sources from output
                    try:
                        if isinstance(out, str):
                            out = json.loads(out)
                        if isinstance(out, dict) and "sources" in out:
                            gathered_sources = out['sources']
                    except Exception:
                        pass

            elif kind == "on_tool_error":
                run_id = ev.get("run_id", "")
                if run_id in tool_calls:
                    tool_calls[run_id]["state"] = "output-error"
                    tool_calls[run_id]["error_text"] = str(
                        ev.get("data", {}).get("error", "Unknown error")
                    )

                    async for chunk in yield_tool_update(run_id):
                        yield chunk

        yield MessageChunk(
            chunk="",
            done=True,
            sources=gathered_sources,
            tools=list(tool_calls.values()),
            response=fix_backticks("".join(buffer_parts)),
        )
