"""CRUD service for managing chats."""

import json
from collections.abc import AsyncGenerator
from contextlib import contextmanager, suppress
from datetime import datetime
from typing import Any, Union
from uuid import uuid4

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from edu_ai.chatbot.context import ChatbotContext
from edu_ai.chatbot.factory import make_chatbot
from edu_db.models import (
    Chat,
    Document,
    Project,
)
from edu_db.models import (
    ChatMessage as DBChatMessage,
)
from edu_db.models import (
    ChatMessagePart as DBChatMessagePart,
)
from edu_db.session import get_session_factory
from langchain_core.messages import AIMessage, BaseMessage, ToolCall, ToolMessage
from langchain_openai import AzureChatOpenAI
from sqlalchemy.orm import joinedload, load_only

from edu_core.exceptions import NotFoundError
from edu_core.schemas.chats import (
    ChatDetailDto,
    ChatDto,
    ChatMessageDto,
    FilePartDto,
    SourceDocumentPartDto,
    StreamingChatMessage,
    TextPartDto,
    ToolCallPartDto,
)


# Constants for part types and tool names
class PartType:
    """Constants for message part types."""

    TEXT = "text"
    FILE = "file"
    TOOL_CALL = "tool_call"
    SOURCE_DOCUMENT = "source-document"


class ToolName:
    """Constants for tool names."""

    SEARCH_PROJECT_DOCUMENTS = "search_project_documents"


class ToolState:
    """Constants for tool call states."""

    INPUT_STREAMING = "input-streaming"
    INPUT_AVAILABLE = "input-available"
    OUTPUT_AVAILABLE = "output-available"
    OUTPUT_ERROR = "output-error"


class ChatService:
    """Service for managing chats with AI-powered responses."""

    def __init__(
        self,
        search_service=None,
        azure_openai_chat_deployment: str | None = None,
        azure_openai_endpoint: str | None = None,
        azure_openai_api_version: str | None = None,
        azure_storage_connection_string: str | None = None,
        usage_service=None,
        queue_service=None,
    ) -> None:
        """Initialize the chat service.

        Args:
            search_service: Optional SearchService for RAG
            azure_openai_chat_deployment: Azure OpenAI chat deployment name
            azure_openai_endpoint: Azure OpenAI endpoint URL
            azure_openai_api_version: Azure OpenAI API version
            azure_storage_connection_string: Azure Storage connection string
            usage_service: Optional usage tracking service
            queue_service: Optional QueueService for async task processing
        """
        self.search_service = search_service
        self.usage_service = usage_service
        self._queue_service = queue_service

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

        self.chatbot = make_chatbot(llm=llm_streaming)

    def _db_part_to_dto(
        self, db_part: DBChatMessagePart
    ) -> Union[TextPartDto, FilePartDto, ToolCallPartDto, SourceDocumentPartDto]:
        """Convert a database message part to a DTO.

        Args:
            db_part: Database message part

        Returns:
            Corresponding DTO part
        """
        if db_part.part_type == PartType.TEXT:
            return TextPartDto(
                id=db_part.id,
                text_content=db_part.text_content,
                order=db_part.order,
            )
        elif db_part.part_type == PartType.FILE:
            # Return blob URL as-is from database (should be full blob URL without SAS token)
            return FilePartDto(
                id=db_part.id,
                file_name=db_part.file_name,
                file_type=db_part.file_type,
                file_url=db_part.file_url or "",
                order=db_part.order,
            )
        elif db_part.part_type == PartType.TOOL_CALL:
            return ToolCallPartDto(
                id=db_part.id,
                tool_call_id=db_part.tool_call_id,
                tool_name=db_part.tool_name,
                tool_input=db_part.tool_input,
                tool_output=db_part.tool_output,
                tool_state=db_part.tool_state,
                order=db_part.order,
            )
        elif db_part.part_type == PartType.SOURCE_DOCUMENT:
            source_id = getattr(db_part, "source_id", None) or ""
            media_type = getattr(db_part, "media_type", None) or "application/pdf"
            source_title = getattr(db_part, "source_title", None) or "Document"
            source_filename = getattr(db_part, "source_filename", None)
            provider_metadata = getattr(db_part, "provider_metadata", None)
            return SourceDocumentPartDto(
                id=db_part.id,
                source_id=source_id,
                media_type=media_type,
                title=source_title,
                filename=source_filename,
                provider_metadata=provider_metadata,
                order=db_part.order,
            )
        else:
            raise ValueError(f"Unknown part type: {db_part.part_type}")

    def _db_message_to_dto(self, db_message: DBChatMessage) -> ChatMessageDto:
        """Convert a database message to a DTO.

        Args:
            db_message: Database message with parts loaded

        Returns:
            ChatMessageDto
        """
        parts_dto = [self._db_part_to_dto(db_part) for db_part in db_message.parts]
        return ChatMessageDto(
            id=db_message.id,
            chat_id=db_message.chat_id,
            role=db_message.role,
            created_at=db_message.created_at,
            parts=parts_dto,
        )

    def _create_source_document_part(
        self,
        source: dict[str, Any],
        db_session,
        existing_source_ids: set[str],
        order: int,
    ) -> SourceDocumentPartDto | None:
        """Create a source document part from a source dict.

        Args:
            source: Source dictionary with document information
            db_session: Database session for querying document metadata
            existing_source_ids: Set of source IDs already added to avoid duplicates
            order: Order index for the part

        Returns:
            SourceDocumentPartDto if created, None if skipped (duplicate or invalid)
        """
        source_id = source.get("id") or source.get("document_id", "")
        if not source_id or source_id in existing_source_ids:
            return None

        # Fetch document metadata if available
        document = (
            db_session.query(Document)
            .filter(Document.id == source.get("document_id"))
            .first()
        )

        # Determine media type from file_type
        file_type = document.file_type if document else "application/pdf"
        media_type_map = {
            "pdf": "application/pdf",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "doc": "application/msword",
            "txt": "text/plain",
            "md": "text/markdown",
        }
        media_type = media_type_map.get(file_type.lower(), "application/pdf")

        return SourceDocumentPartDto(
            source_id=source_id,
            media_type=media_type,
            title=source.get("title", document.file_name if document else "Document"),
            filename=document.file_name if document else None,
            provider_metadata={
                "document_id": source.get("document_id"),
                "score": source.get("score"),
            }
            if source.get("score")
            else None,
            order=order,
        )

    def _convert_messages_to_llm_format(
        self, messages: list[ChatMessageDto]
    ) -> list[dict[str, Any]]:
        """Convert ChatMessageDto list to LLM-compatible format.

        Args:
            messages: List of ChatMessageDto

        Returns:
            List of dictionaries with role and content for LLM
        """
        llm_chat_history = []
        for msg_dto in messages:
            content_parts = []
            for part_dto in msg_dto.parts:
                if isinstance(part_dto, TextPartDto):
                    content_parts.append(
                        {"type": "text", "text": part_dto.text_content}
                    )
                elif isinstance(part_dto, FilePartDto):
                    # Filter out file parts - file upload is not supported
                    continue
            llm_chat_history.append({"role": msg_dto.role, "content": content_parts})
        return llm_chat_history

    def _extract_sources_from_chunk(
        self, chunk: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Extract sources from a stream chunk.

        Args:
            chunk: Stream chunk dictionary

        Returns:
            List of source dictionaries
        """
        sources = []
        if "ensure_sources_in_stream.after_model" in chunk:
            middleware_data = chunk.get("ensure_sources_in_stream.after_model") or {}
            sources = middleware_data.get("sources", [])
        elif "sources" in chunk:
            sources = chunk.get("sources", [])
        return sources

    def _extract_sources_from_tool_message(
        self, msg: ToolMessage
    ) -> list[dict[str, Any]]:
        """Extract sources from a tool message.

        Args:
            msg: ToolMessage from the stream

        Returns:
            List of source dictionaries
        """
        sources = []
        content = msg.content
        content_dict = None

        # Try to parse as JSON first
        if isinstance(content, str):
            with suppress(json.JSONDecodeError, TypeError):
                content_dict = json.loads(content)
        elif isinstance(content, dict):
            content_dict = content

        # Extract sources if available
        if content_dict and isinstance(content_dict, dict):
            sources = content_dict.get("sources", [])

        # If no sources in content, try to get from tool result metadata
        if not sources and hasattr(msg, "additional_kwargs") and msg.additional_kwargs:
            sources = msg.additional_kwargs.get("sources", [])

        return sources

    def _handle_message_stream_chunk(
        self,
        message: AIMessage,
        current_parts: list[
            Union[TextPartDto, FilePartDto, ToolCallPartDto, SourceDocumentPartDto]
        ],
        accumulated_text: str,
        text_part_id: str | None,
        assistant_message_id: str,
        chat_id: str,
        has_started_generating: bool,
    ) -> tuple[
        list[Union[TextPartDto, FilePartDto, ToolCallPartDto, SourceDocumentPartDto]],
        str,
        str | None,
        bool,
        StreamingChatMessage | None,
    ]:
        """Handle a message stream chunk and update state.

        Args:
            message: AIMessage from the stream
            current_parts: Current list of parts
            accumulated_text: Accumulated text so far
            text_part_id: Current text part ID
            assistant_message_id: Assistant message ID
            chat_id: Chat ID
            has_started_generating: Whether generation has started

        Returns:
            Tuple of (updated_parts, updated_accumulated_text, updated_text_part_id, updated_has_started_generating, streaming_message_or_none)
        """
        if not (hasattr(message, "content") and message.content):
            return (
                current_parts,
                accumulated_text,
                text_part_id,
                has_started_generating,
                None,
            )

        # Accumulate text for final message
        new_accumulated_text = accumulated_text + message.content

        # Find or create a TextPartDto
        text_part_index = next(
            (i for i, p in enumerate(current_parts) if isinstance(p, TextPartDto)),
            -1,
        )

        if text_part_index == -1:
            # First chunk - create new part with unique ID
            new_text_part_id = str(uuid4())
            new_text_part = TextPartDto(
                id=new_text_part_id,
                text_content=new_accumulated_text,
                order=len(current_parts),
            )
            current_parts.append(new_text_part)
            updated_text_part_id = new_text_part_id
        else:
            # Update accumulated text in current_parts for final message
            current_parts[text_part_index].text_content = new_accumulated_text
            # Ensure part has ID
            if not current_parts[text_part_index].id:
                updated_text_part_id = str(uuid4())
                current_parts[text_part_index].id = updated_text_part_id
            else:
                updated_text_part_id = current_parts[text_part_index].id

        # Create streaming parts with delta only (similar to Vercel AI SDK)
        streaming_parts = []
        for part in current_parts:
            if isinstance(part, TextPartDto):
                # Send only the delta (new content) for text parts with part ID
                streaming_parts.append(
                    TextPartDto(
                        id=updated_text_part_id,
                        text_content=message.content,  # Delta only
                        order=part.order,
                    )
                )
            else:
                # For non-text parts, send as-is (ensure they have IDs)
                if not part.id:
                    part.id = str(uuid4())
                streaming_parts.append(part)

        streaming_message = StreamingChatMessage(
            id=assistant_message_id,
            chat_id=chat_id,
            role="assistant",
            created_at=datetime.now(),
            parts=streaming_parts,
            done=False,
            status="generating" if not has_started_generating else None,
        )

        updated_has_started_generating = True

        return (
            current_parts,
            new_accumulated_text,
            updated_text_part_id,
            updated_has_started_generating,
            streaming_message,
        )

    def _process_user_message_parts(
        self,
        parts: list[dict[str, Any]],
        user_message_db: DBChatMessage,
        db,
    ) -> tuple[list[Union[TextPartDto, FilePartDto]], list[str]]:
        """Process user message parts and save to database.

        Args:
            parts: List of part dictionaries from the request
            user_message_db: Database message object to associate parts with
            db: Database session

        Returns:
            Tuple of (parts_dto_list, text_content_parts_list)
        """
        user_parts_dto = []
        text_content_parts = []

        for part_index, part_dict in enumerate(parts):
            part_type = part_dict.get("type", PartType.TEXT)

            # Filter out file parts - file upload is not supported
            if part_type == PartType.FILE:
                continue

            if part_type == PartType.TEXT:
                db_part = DBChatMessagePart(
                    id=str(uuid4()),
                    message_id=user_message_db.id,
                    part_type=part_type,
                    order=part_index,
                )
                text_content = part_dict.get("text", "")
                db_part.text_content = text_content
                text_content_parts.append(text_content)
                user_parts_dto.append(
                    TextPartDto(
                        text_content=text_content,
                        order=part_index,
                    )
                )
                db.add(db_part)

        return user_parts_dto, text_content_parts

    def create_chat(
        self,
        project_id: str,
        user_id: str,
        title: str | None = None,
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
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                )

                db.add(chat)
                db.commit()
                db.refresh(chat)

                return self._model_to_dto(chat)
            except Exception:
                db.rollback()
                raise

    def _convert_blob_url_to_proxy_url(self, blob_url: str | None) -> str | None:
        """Convert Azure blob URL to proxy URL.

        Args:
            blob_url: Azure blob URL (e.g., https://account.blob.core.windows.net/container/path)
                      or blob path (e.g., project_id/chat_id/filename)

        Returns:
            Proxy URL (e.g., /api/v1/blobs/project_id/chat_id/filename) or None if invalid
        """
        if not blob_url:
            return None

        # If it's already a relative path (no http/https), use it directly
        if not blob_url.startswith("http://") and not blob_url.startswith("https://"):
            return f"/api/v1/blobs/{blob_url}"

        # If it's a full Azure blob URL, extract the blob path
        # Format: https://{account}.blob.core.windows.net/{container}/{blob_path}
        if ".blob.core.windows.net/" in blob_url:
            # Remove query parameters (SAS tokens)
            blob_url = blob_url.split("?")[0]
            # Extract blob path after container name
            parts = blob_url.split(".blob.core.windows.net/")
            if len(parts) == 2:
                # parts[1] is "{container}/{blob_path}"
                container_and_path = parts[1]
                # Find the first slash to separate container from path
                first_slash = container_and_path.find("/")
                if first_slash != -1:
                    blob_path = container_and_path[first_slash + 1 :]
                    return f"/api/v1/blobs/{blob_path}"

        # If we can't parse it, return None
        return None

    def get_chat(
        self, chat_id: str, user_id: str, include_messages: bool = False
    ) -> ChatDto | ChatDetailDto:
        """Get a chat by ID, optionally with messages.

        Args:
            chat_id: The chat ID
            user_id: The user ID
            include_messages: Whether to include messages and parts

        Returns:
            ChatDto or ChatDetailDto (if include_messages=True)

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

                if not include_messages:
                    return self._model_to_dto(chat)

                # Fetch messages with parts
                db_messages = (
                    db.query(DBChatMessage)
                    .filter(DBChatMessage.chat_id == chat_id)
                    .options(
                        joinedload(DBChatMessage.parts).options(
                            load_only(
                                DBChatMessagePart.id,
                                DBChatMessagePart.message_id,
                                DBChatMessagePart.part_type,
                                DBChatMessagePart.order,
                                DBChatMessagePart.text_content,
                                DBChatMessagePart.file_name,
                                DBChatMessagePart.file_type,
                                DBChatMessagePart.file_url,
                                DBChatMessagePart.tool_call_id,
                                DBChatMessagePart.tool_name,
                                DBChatMessagePart.tool_input,
                                DBChatMessagePart.tool_output,
                                DBChatMessagePart.tool_state,
                                DBChatMessagePart.created_at,
                            )
                        )
                    )
                    .order_by(DBChatMessage.created_at)
                    .all()
                )

                # Convert messages to DTOs
                messages_dto = [
                    self._db_message_to_dto(db_msg) for db_msg in db_messages
                ]

                # Create ChatDetailDto with messages
                chat_dto = self._model_to_dto(chat)
                return ChatDetailDto(
                    id=chat_dto.id,
                    project_id=chat_dto.project_id,
                    user_id=chat_dto.user_id,
                    title=chat_dto.title,
                    created_at=chat_dto.created_at,
                    updated_at=chat_dto.updated_at,
                    messages=messages_dto,
                )
            except NotFoundError:
                raise
            except Exception:
                raise

    def list_chats(self, project_id: str, user_id: str) -> list[ChatDto]:
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
            except Exception:
                raise

    def update_chat(
        self,
        chat_id: str,
        user_id: str,
        title: str | None = None,
    ) -> ChatDto:
        """Update a chat.

        Args:
            chat_id: The chat ID
            user_id: The user ID
            title: Optional new title

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
            except Exception:
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
            except Exception:
                db.rollback()
                raise

    def _model_to_dto(self, chat: Chat) -> ChatDto:
        """Convert Chat model to ChatDto."""
        # ChatDto no longer contains messages directly. Messages are fetched separately.
        chat_dto = ChatDto(
            id=chat.id,
            project_id=chat.project_id,
            user_id=chat.user_id,
            title=chat.title,
            created_at=chat.created_at,
            updated_at=chat.updated_at,
        )

        return chat_dto

    async def send_streaming_message(
        self, chat_id: str, user_id: str, parts: list[dict[str, Any]]
    ) -> AsyncGenerator[StreamingChatMessage]:
        """Send a streaming message to a chat using grounded RAG responses.

        Args:
            chat_id: The chat ID
            user_id: The user's ID
            message_content: The text content of the message to send

        Yields:
            StreamingChatMessage instances containing message chunks and metadata
        """
        if not self.chatbot:
            raise ValueError(
                "Agent not initialized. SearchService and Azure OpenAI config required."
            )

        with self._get_db_session() as db:
            # Generate message ID for assistant early so it's available in error handler
            assistant_message_id = str(uuid4())
            try:
                chat = (
                    db.query(Chat)
                    .filter(Chat.id == chat_id, Chat.user_id == user_id)
                    .first()
                )
                if not chat:
                    raise NotFoundError(f"Chat {chat_id} not found")

                # Fetch all previous messages and their parts
                db_messages = (
                    db.query(DBChatMessage)
                    .filter(DBChatMessage.chat_id == chat_id)
                    .options(joinedload(DBChatMessage.parts))  # Eagerly load parts
                    .order_by(DBChatMessage.created_at)
                    .all()
                )

                # Convert DB messages to DTOs for the chatbot context
                chat_history_for_llm = [
                    self._db_message_to_dto(db_msg) for db_msg in db_messages
                ]

                is_first_message = len(chat_history_for_llm) == 0

                # Save user message to DB
                user_message_db = DBChatMessage(
                    id=str(uuid4()), chat_id=chat_id, role="user"
                )
                db.add(user_message_db)
                db.flush()  # To get user_message_db.id for the part

                # Process parts and save to DB
                user_parts_dto, text_content_parts = self._process_user_message_parts(
                    parts, user_message_db, db
                )
                db.commit()

                # Get project language code
                project = (
                    db.query(Project).filter(Project.id == chat.project_id).first()
                )
                language_code = (
                    getattr(project, "language_code", "en") if project else "en"
                )

                # Build query string from text parts for backward compatibility
                query = " ".join(text_content_parts) if text_content_parts else ""

                # Add user message to chat history for LLM
                user_chat_message_dto = ChatMessageDto(
                    id=user_message_db.id,
                    chat_id=chat_id,
                    role="user",
                    created_at=user_message_db.created_at,
                    parts=user_parts_dto,
                )
                chat_history_for_llm.append(user_chat_message_dto)

                # Stream the response
                async for stream_chunk in self._get_response_stream(
                    query=query,
                    messages=chat_history_for_llm,
                    language_code=language_code,
                    project_id=chat.project_id,
                    user_id=user_id,
                    assistant_message_id=assistant_message_id,
                    db_session=db,
                ):
                    # If this is the final chunk, save the complete message to database
                    if stream_chunk.done:
                        assistant_message_db = DBChatMessage(
                            id=assistant_message_id,
                            chat_id=chat_id,
                            role="assistant",
                        )
                        db.add(assistant_message_db)
                        db.flush()  # Ensure ID is available for parts

                        for part_index, part_dto in enumerate(stream_chunk.parts):
                            db_part = DBChatMessagePart(
                                id=str(uuid4()),
                                message_id=assistant_message_db.id,
                                part_type=part_dto.type,
                                order=part_index,
                            )
                            if isinstance(part_dto, TextPartDto):
                                db_part.text_content = part_dto.text_content
                            elif isinstance(part_dto, FilePartDto):
                                # Strip SAS token from URL before persisting
                                file_url = part_dto.file_url
                                if file_url and "?" in file_url:
                                    file_url = file_url.split("?")[0]

                                db_part.file_name = part_dto.file_name
                                db_part.file_type = part_dto.file_type
                                db_part.file_url = file_url
                            elif isinstance(part_dto, ToolCallPartDto):
                                db_part.tool_call_id = part_dto.tool_call_id
                                db_part.tool_name = part_dto.tool_name
                                db_part.tool_input = part_dto.tool_input
                                db_part.tool_output = part_dto.tool_output
                                db_part.tool_state = part_dto.tool_state
                            elif isinstance(part_dto, SourceDocumentPartDto):
                                db_part.source_id = part_dto.source_id
                                db_part.media_type = part_dto.media_type
                                db_part.source_title = part_dto.title
                                db_part.source_filename = part_dto.filename
                                db_part.provider_metadata = part_dto.provider_metadata
                            db.add(db_part)

                        # Queue title generation for first message
                        if is_first_message:
                            # Extract text content from user message parts
                            user_message_text = " ".join(
                                [
                                    p.text_content
                                    for p in user_parts_dto
                                    if isinstance(p, TextPartDto)
                                ]
                            )

                            # Extract AI response text
                            ai_response_text = "".join(
                                [
                                    p.text_content
                                    for p in stream_chunk.parts
                                    if isinstance(p, TextPartDto)
                                ]
                            )

                            # Try to get queue_service from the service instance
                            # If not available, fall back to synchronous generation
                            queue_service = getattr(self, "_queue_service", None)
                            if queue_service:
                                from edu_queue.schemas import (
                                    ChatTitleGenerationData,
                                    QueueTaskMessage,
                                    TaskType,
                                )

                                task_data: ChatTitleGenerationData = {
                                    "chat_id": chat_id,
                                    "project_id": chat.project_id,
                                    "user_id": user_id,
                                    "user_message": user_message_text,
                                    "ai_response": ai_response_text,
                                }

                                task_message: QueueTaskMessage = {
                                    "type": TaskType.CHAT_TITLE_GENERATION,
                                    "data": task_data,
                                }
                                queue_service.send_message(task_message)
                            else:
                                # Fallback to synchronous generation if queue not available
                                generated_title = await self._generate_chat_title(
                                    user_message_text,
                                    ai_response_text,
                                )
                                chat.title = generated_title

                        chat.updated_at = datetime.now()
                        db.commit()

                    yield stream_chunk

            except Exception as e:
                # Use the pre-generated assistant_message_id for error messages
                error_parts = [TextPartDto(text_content=f"Error: {e!s}")]
                yield StreamingChatMessage(
                    id=assistant_message_id,
                    chat_id=chat_id,
                    role="assistant",
                    created_at=datetime.now(),
                    parts=error_parts,
                    done=True,
                )

    async def _get_response_stream(
        self,
        query: str,
        messages: list[ChatMessageDto],
        project_id: str,
        language_code: str,
        user_id: str | None = None,
        assistant_message_id: str | None = None,
        db_session=None,
    ) -> AsyncGenerator[StreamingChatMessage]:
        """Get response stream from agent.

        Args:
            query: The user's query
            messages: List of previous chat messages (ChatMessageDto)
            project_id: The project ID
            language_code: Language code for responses
            user_id: Optional user ID
            assistant_message_id: The ID of the assistant message being streamed

        Yields:
            StreamingChatMessage instances containing response chunks and metadata
        """
        # Convert ChatMessageDto to LLM-compatible chat_history
        llm_chat_history = self._convert_messages_to_llm_format(messages)

        # --- agent + state ------------------------------------------------------
        current_parts: list[
            Union[TextPartDto, FilePartDto, ToolCallPartDto, SourceDocumentPartDto]
        ] = []
        tool_calls: dict[str, ToolCallPartDto] = {}
        has_started_generating = False
        # Track accumulated text separately for final message
        accumulated_text = ""
        # Track part IDs for streaming (similar to Vercel AI SDK)
        text_part_id: str | None = None

        ctx = ChatbotContext(
            project_id=project_id,
            user_id=user_id or "",
            usage=self.usage_service,
            search=self.search_service,
            queue=self._queue_service,
            language=language_code,
            llm=self.llm_non_streaming,  # Use non-streaming LLM for tools
        )

        # Send initial "thinking" status with start message
        # Similar to Vercel AI SDK's start message part
        yield StreamingChatMessage(
            id=assistant_message_id,
            chat_id=messages[0].chat_id
            if messages
            else "",  # This will be filled later, or from initial message
            role="assistant",
            created_at=datetime.now(),
            parts=[],  # Empty parts for start message
            done=False,
            status="thinking",
        )

        # --- process stream chunks ----------------------------------------------
        async for chunk in self.chatbot.astream(
            {"messages": llm_chat_history, "sources": []},  # Pass llm_chat_history
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
                        if (
                            isinstance(metadata, dict)
                            and metadata.get("langgraph_node") == "tools"
                        ):
                            continue

                        # Skip ToolMessage content - tool outputs should only be sent via tools field
                        if isinstance(message, ToolMessage):
                            continue

                        # Only stream AIMessage content (agent responses)
                        if isinstance(message, AIMessage):
                            chat_id = messages[0].chat_id if messages else ""
                            (
                                current_parts,
                                accumulated_text,
                                text_part_id,
                                has_started_generating,
                                streaming_message,
                            ) = self._handle_message_stream_chunk(
                                message,
                                current_parts,
                                accumulated_text,
                                text_part_id,
                                assistant_message_id,
                                chat_id,
                                has_started_generating,
                            )
                            if streaming_message:
                                yield streaming_message
                    continue

                # Handle "updates" mode - node completions
                elif mode_name == "updates":
                    chunk = data  # data is the actual update dict, continue processing below
                else:
                    continue

            # Handle update-level chunks (node completions) - must be a dict from here on
            if not isinstance(chunk, dict):
                continue

            # Extract sources from middleware hooks and create source-document parts
            sources = self._extract_sources_from_chunk(chunk)

            if sources and db_session:
                existing_source_ids = {
                    p.source_id
                    for p in current_parts
                    if isinstance(p, SourceDocumentPartDto)
                }
                initial_source_count = len(existing_source_ids)
                chat_id = messages[0].chat_id if messages else ""

                # Create source-document parts
                for source in sources:
                    source_part = self._create_source_document_part(
                        source, db_session, existing_source_ids, len(current_parts)
                    )
                    if source_part:
                        current_parts.append(source_part)
                        existing_source_ids.add(source_part.source_id)

                # Yield update with source-document parts if any were added
                if len(existing_source_ids) > initial_source_count:
                    yield StreamingChatMessage(
                        id=assistant_message_id,
                        chat_id=chat_id,
                        role="assistant",
                        created_at=datetime.now(),
                        parts=current_parts.copy(),
                        done=False,
                    )

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

                            # Skip creating tool_call parts for RAG - it will create source-document parts instead
                            if tc_name == ToolName.SEARCH_PROJECT_DOCUMENTS:
                                # Track the tool call but don't create a part
                                tool_calls[tc_id] = {
                                    "tool_name": tc_name,
                                    "tool_input": tc_args,
                                }
                                continue

                            # Create or update tool call entry for non-RAG tools
                            if tc_id not in tool_calls:
                                tool_calls[tc_id] = ToolCallPartDto(
                                    tool_call_id=tc_id,
                                    tool_name=tc_name,
                                    tool_input=tc_args,
                                    tool_state=ToolState.INPUT_AVAILABLE,
                                    order=len(current_parts),
                                )
                                current_parts.append(tool_calls[tc_id])
                            elif not tool_calls[tc_id].tool_input:
                                tool_calls[tc_id].tool_input = tc_args

                            # Yield update with tool call parts
                            yield StreamingChatMessage(
                                id=assistant_message_id,
                                chat_id=messages[0].chat_id if messages else "",
                                role="assistant",
                                created_at=datetime.now(),
                                parts=current_parts.copy(),
                                done=False,
                            )

            # Handle tool execution results from tools node
            if "tools" in chunk:
                msgs: list[BaseMessage] = chunk["tools"].get("messages", [])

                for msg in msgs:
                    if isinstance(msg, ToolMessage):
                        tc_id = msg.tool_call_id

                        if tc_id in tool_calls:
                            tool_call_info = tool_calls[tc_id]

                            # Handle RAG tool results - extract sources and create source-document parts
                            if (
                                isinstance(tool_call_info, dict)
                                and tool_call_info.get("tool_name")
                                == ToolName.SEARCH_PROJECT_DOCUMENTS
                            ):
                                # Extract sources from tool message content
                                try:
                                    sources = self._extract_sources_from_tool_message(
                                        msg
                                    )

                                    # Create source-document parts if we have sources
                                    if sources and db_session:
                                        existing_source_ids = {
                                            p.source_id
                                            for p in current_parts
                                            if isinstance(p, SourceDocumentPartDto)
                                        }
                                        initial_source_count = len(existing_source_ids)
                                        chat_id = (
                                            messages[0].chat_id if messages else ""
                                        )

                                        # Create source-document parts
                                        for source in sources:
                                            source_part = (
                                                self._create_source_document_part(
                                                    source,
                                                    db_session,
                                                    existing_source_ids,
                                                    len(current_parts),
                                                )
                                            )
                                            if source_part:
                                                current_parts.append(source_part)
                                                existing_source_ids.add(
                                                    source_part.source_id
                                                )

                                        # Yield update with source-document parts if any were added
                                        if (
                                            len(existing_source_ids)
                                            > initial_source_count
                                        ):
                                            yield StreamingChatMessage(
                                                id=assistant_message_id,
                                                chat_id=chat_id,
                                                role="assistant",
                                                created_at=datetime.now(),
                                                parts=current_parts.copy(),
                                                done=False,
                                            )
                                except Exception:
                                    pass

                                # No need to create tool_call parts for RAG
                                continue

                            # Handle non-RAG tool results - update tool_call parts
                            elif isinstance(tool_call_info, ToolCallPartDto):
                                # Check if there's an error in the status
                                if msg.status == "error":
                                    tool_call_info.tool_state = ToolState.OUTPUT_ERROR
                                    tool_call_info.tool_output = {
                                        "error": str(msg.content)
                                    }
                                else:
                                    tool_call_info.tool_state = (
                                        ToolState.OUTPUT_AVAILABLE
                                    )
                                    tool_call_info.tool_output = msg.content

                                # Yield update with tool call parts
                                yield StreamingChatMessage(
                                    id=assistant_message_id,
                                    chat_id=messages[0].chat_id if messages else "",
                                    role="assistant",
                                    created_at=datetime.now(),
                                    parts=current_parts.copy(),
                                    done=False,
                                )

        # --- finalize -----------------------------------------------------------
        # Ensure final yield contains all accumulated parts and done=True
        final_parts = current_parts.copy()
        yield StreamingChatMessage(
            id=assistant_message_id,
            chat_id=messages[0].chat_id if messages else "",
            role="assistant",
            created_at=datetime.now(),
            parts=final_parts,
            done=True,
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

    def upload_chat_file(
        self, file_content: bytes, filename: str, project_id: str, chat_id: str
    ) -> str:
        """Upload a file for a chat message.

        Args:
            file_content: The file content as bytes
            filename: Name of the file
            project_id: The project ID
            chat_id: The chat ID

        Returns:
            URL of the uploaded file

        Raises:
            Exception: If blob storage is not configured or upload fails
        """
        if not self.blob_service_client or not self.chat_files_container:
            raise Exception("Blob storage not configured for chat service.")

        try:
            blob_name = f"{project_id}/{chat_id}/{uuid4()}-{filename}"
            blob_client = self.blob_service_client.get_blob_client(
                container=self.chat_files_container, blob=blob_name
            )
            blob_client.upload_blob(data=file_content, overwrite=True)
            return blob_client.url
        except Exception as e:
            # In a real app, you'd want more specific error handling
            raise Exception(f"Failed to upload chat file: {e}") from e

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
