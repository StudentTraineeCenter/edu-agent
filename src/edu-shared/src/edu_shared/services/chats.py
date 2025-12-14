"""CRUD service for managing chats."""

from contextlib import contextmanager
from datetime import datetime
from typing import AsyncGenerator, List, Optional
from uuid import uuid4

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from langchain_core.messages import AIMessage, BaseMessage, ToolCall, ToolMessage
from langchain_openai import AzureChatOpenAI

from edu_shared.agents.context import CustomAgentContext
from edu_shared.agents.factory import make_agent
from edu_shared.db.models import Chat, ChatMessage, ChatMessageSource, ChatMessageToolCall
from edu_shared.db.session import get_session_factory
from edu_shared.schemas.chats import ChatDto, ChatMessageDto, SourceDto, ToolCallDto
from edu_shared.exceptions import NotFoundError


from pydantic import BaseModel, Field

class MessageChunk(BaseModel):
    """Internal model for streaming message chunks."""

    chunk: str = Field(default="", description="Text chunk of the response")
    done: bool = Field(default=False, description="Whether this is the final chunk")
    status: Optional[str] = Field(default=None, description="Status message for this chunk (e.g., thinking, searching, etc.)")
    sources: Optional[List[ChatMessageSource]] = Field(default_factory=list, description="Source document objects, if any")
    tools: Optional[List] = Field(default_factory=list, description="Associated tool call objects, if any")
    id: Optional[str] = Field(default=None, description="Optional message id")
    response: Optional[str] = Field(default=None, description="Full concatenated response, present in final chunk if desired")


class ChatService:
    """Service for managing chats with AI-powered responses."""

    def __init__(
        self,
        search_service=None,
        azure_openai_chat_deployment: Optional[str] = None,
        azure_openai_endpoint: Optional[str] = None,
        azure_openai_api_version: Optional[str] = None,
        usage_service=None,
    ) -> None:
        """Initialize the chat service.
        
        Args:
            search_service: Optional SearchService for RAG
            azure_openai_chat_deployment: Azure OpenAI chat deployment name
            azure_openai_endpoint: Azure OpenAI endpoint URL
            azure_openai_api_version: Azure OpenAI API version
            usage_service: Optional usage tracking service
        """
        self.search_service = search_service
        self.usage_service = usage_service
        
        # Initialize LLM instances
        self.credential = DefaultAzureCredential()
        self.token_provider = get_bearer_token_provider(
            self.credential, "https://cognitiveservices.azure.com/.default"
        )
        
        # Build LLM kwargs, only include api_version if provided
        llm_kwargs = {
            "azure_deployment": azure_openai_chat_deployment,
            "azure_endpoint": azure_openai_endpoint,
            "azure_ad_token_provider": self.token_provider,
            "temperature": 0.25,
        }
        if azure_openai_api_version:
            llm_kwargs["api_version"] = azure_openai_api_version
        
        llm_streaming = AzureChatOpenAI(
            streaming=True,
            **llm_kwargs,
        )
        
        self.llm_non_streaming = AzureChatOpenAI(
            streaming=False,
            **llm_kwargs,
        )

        self.agent = make_agent(llm=llm_streaming)            

    def create_chat(
        self,
        project_id: str,
        user_id: str,
        title: Optional[str] = None,
    ) -> ChatDto:
        """Create a new chat.

        Args:
            project_id: The project ID
            user_id: The user ID
            title: Optional chat title

        Returns:
            Created ChatDto
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

                db.add(chat)
                db.commit()
                db.refresh(chat)

                return self._model_to_dto(chat)
            except Exception as e:
                db.rollback()
                raise

    def get_chat(self, chat_id: str, user_id: str) -> ChatDto:
        """Get a chat by ID.

        Args:
            chat_id: The chat ID
            user_id: The user ID

        Returns:
            ChatDto

        Raises:
            NotFoundError: If chat not found
        """
        with self._get_db_session() as db:
            try:
                chat = (
                    db.query(Chat)
                    .filter(Chat.id == chat_id, Chat.user_id == user_id)
                    .first()
                )
                if not chat:
                    raise NotFoundError(f"Chat {chat_id} not found")

                return self._model_to_dto(chat)
            except NotFoundError:
                raise
            except Exception as e:
                raise

    def list_chats(self, project_id: str, user_id: str) -> List[ChatDto]:
        """List all chats for a project.

        Args:
            project_id: The project ID
            user_id: The user ID

        Returns:
            List of ChatDto instances
        """
        with self._get_db_session() as db:
            try:
                chats = (
                    db.query(Chat)
                    .filter(Chat.project_id == project_id, Chat.user_id == user_id)
                    .order_by(Chat.created_at.desc())
                    .all()
                )
                return [self._model_to_dto(chat) for chat in chats]
            except Exception as e:
                raise

    def update_chat(
        self,
        chat_id: str,
        user_id: str,
        title: Optional[str] = None,
    ) -> ChatDto:
        """Update a chat.

        Args:
            chat_id: The chat ID
            user_id: The user ID
            title: Optional new title
            messages: Optional new messages list

        Returns:
            Updated ChatDto

        Raises:
            NotFoundError: If chat not found
        """
        with self._get_db_session() as db:
            try:
                chat = (
                    db.query(Chat)
                    .filter(Chat.id == chat_id, Chat.user_id == user_id)
                    .first()
                )
                if not chat:
                    raise NotFoundError(f"Chat {chat_id} not found")

                if title is not None:
                    chat.title = title
                
                chat.updated_at = datetime.now()

                db.commit()
                db.refresh(chat)

                return self._model_to_dto(chat)
            except NotFoundError:
                raise
            except Exception as e:
                db.rollback()
                raise

    def delete_chat(self, chat_id: str, user_id: str) -> None:
        """Delete a chat.

        Args:
            chat_id: The chat ID
            user_id: The user ID

        Raises:
            NotFoundError: If chat not found
        """
        with self._get_db_session() as db:
            try:
                chat = (
                    db.query(Chat)
                    .filter(Chat.id == chat_id, Chat.user_id == user_id)
                    .first()
                )
                if not chat:
                    raise NotFoundError(f"Chat {chat_id} not found")

                db.delete(chat)
                db.commit()
            except NotFoundError:
                raise
            except Exception as e:
                db.rollback()
                raise

    def _model_to_dto(self, chat: Chat) -> ChatDto:
        """Convert Chat model to ChatDto."""
        from datetime import datetime

        messages = []
        # Messages are stored as JSON (list of dicts)
        for msg_dict in chat.messages:
            # Parse created_at if it's a string
            created_at = msg_dict.get("created_at")
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            elif not isinstance(created_at, datetime):
                created_at = datetime.now()

            messages.append(
                ChatMessageDto(
                    id=msg_dict["id"],
                    role=msg_dict["role"],
                    content=msg_dict["content"],
                    sources=[
                        SourceDto(
                            id=src["id"],
                            content=src["content"],
                            title=src["title"],
                            document_id=src["document_id"],
                        )
                        for src in (msg_dict.get("sources") or [])
                    ]
                    if msg_dict.get("sources")
                    else None,
                    tools=[
                        ToolCallDto(
                            id=tool["id"],
                            type=tool["type"],
                            name=tool["name"],
                            state=tool["state"],
                            input=tool.get("input"),
                            output=tool.get("output"),
                            error_text=tool.get("error_text"),
                        )
                        for tool in (msg_dict.get("tools") or [])
                    ]
                    if msg_dict.get("tools")
                    else None,
                    created_at=created_at,
                )
            )

        return ChatDto(
            id=chat.id,
            project_id=chat.project_id,
            user_id=chat.user_id,
            title=chat.title,
            messages=messages,
            created_at=chat.created_at,
            updated_at=chat.updated_at,
        )

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
        if not self.agent:
            raise ValueError("Agent not initialized. SearchService and Azure OpenAI config required.")
        
        with self._get_db_session() as db:
            # Generate message ID early so it's available in error handler
            assistant_message_id = str(uuid4())
            try:
                chat = (
                    db.query(Chat)
                    .filter(Chat.id == chat_id, Chat.user_id == user_id)
                    .first()
                )
                if not chat:
                    raise NotFoundError(f"Chat {chat_id} not found")

                # Get project language code
                from edu_shared.db.models import Project
                project = db.query(Project).filter(Project.id == chat.project_id).first()
                language_code = getattr(project, "language_code", "en") if project else "en"

                messages = [ChatMessage(**msg) for msg in chat.messages]
                is_first_message = len(messages) == 0

                # Stream the response
                async for chunk_data in self._get_response_stream(
                    query=message,
                    messages=messages,
                    language_code=language_code,
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

                        chat.updated_at = datetime.now()
                        db.commit()

                    # Yield chunk with message_id
                    chunk_data.id = assistant_message_id
                    yield chunk_data
            except Exception as e:
                # Use the pre-generated assistant_message_id for error messages
                yield MessageChunk(
                    chunk=f"Error: {str(e)}",
                    done=True,
                    sources=[],
                    tools=[],
                    id=assistant_message_id,
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
        chat_history = [{"role": m.role, "content": m.content} for m in messages]

        async def yield_tool_update():
            yield MessageChunk(chunk="", done=False, tools=list(tool_calls.values()))

        # --- agent + state ------------------------------------------------------

        buffer_parts: list[str] = []
        gathered_sources: list[ChatMessageSource] = []
        tool_calls: dict[str, ChatMessageToolCall] = {}
        has_started_generating = False

        chat_history.append({"role": "user", "content": query})

        ctx = CustomAgentContext(
            project_id=project_id,
            user_id=user_id or "",
            usage=self.usage_service,
            search=self.search_service,
            language=language_code,
            llm=self.llm_non_streaming,  # Use non-streaming LLM for tools
        )

        # Send initial "thinking" status
        yield MessageChunk(chunk="", done=False, status="thinking")

        # --- process stream chunks ----------------------------------------------
        async for chunk in self.agent.astream(
            {"messages": chat_history, "sources": []},
            stream_mode=["updates", "messages"],
            context=ctx,
        ):
            # When using stream_mode=["updates", "messages"], chunks come as (mode_name, data)
            if isinstance(chunk, tuple) and len(chunk) == 2:
                mode_name, data = chunk

                # Handle "messages" mode - token-by-token streaming
                if mode_name == "messages":
                    # data is a tuple of (message, metadata)
                    if isinstance(data, tuple) and len(data) == 2:
                        message, metadata = data

                        # Skip messages from tools node - tool outputs should only be sent via tools field
                        if isinstance(metadata, dict) and metadata.get("langgraph_node") == "tools":
                            continue

                        # Skip ToolMessage content - tool outputs should only be sent via tools field
                        if isinstance(message, ToolMessage):
                            continue

                        # Only stream AIMessage content (agent responses)
                        if (
                            isinstance(message, AIMessage)
                            and hasattr(message, "content")
                            and message.content
                        ):
                            buffer_parts.append(message.content)
                            yield MessageChunk(chunk=message.content, done=False)

                            # Send "generating" status on first token
                            if not has_started_generating:
                                yield MessageChunk(
                                    chunk="", done=False, status="generating"
                                )
                                has_started_generating = True
                    continue

                # Handle "updates" mode - node completions
                elif mode_name == "updates":
                    chunk = data  # data is the actual update dict, continue processing below
                else:
                    continue

            # Handle update-level chunks (node completions) - must be a dict from here on
            if not isinstance(chunk, dict):
                continue

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

                for source in model_sources:
                    if not any(s.id == source.id for s in gathered_sources):
                        gathered_sources.append(source)

            # Handle model chunks (node completions - tool calls and metadata)
            if "model" in chunk:
                msgs: list[BaseMessage] = chunk["model"].get("messages", [])

                for msg in msgs:
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

            # Handle tool execution results from tools node
            if "tools" in chunk:
                msgs: list[BaseMessage] = chunk["tools"].get("messages", [])

                for msg in msgs:
                    if isinstance(msg, ToolMessage):
                        tc_id = msg.tool_call_id

                        if tc_id in tool_calls:
                            # Check if there's an error in the status
                            if msg.status == "error":
                                tool_calls[tc_id].state = "output-error"
                                tool_calls[tc_id].error_text = str(msg.content)
                            else:
                                tool_calls[tc_id].state = "output-available"
                                tool_calls[tc_id].output = msg.content

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
        except Exception:
            return "New Chat"

    @contextmanager
    def _get_db_session(self):
        """Context manager for database sessions."""
        SessionLocal = get_session_factory()
        db = SessionLocal()
        try:
            yield db
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

