from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

# ============================================================================
# Internal Service Layer Types
# ============================================================================


class MessageChunk(BaseModel):
    """Model for streaming message chunks."""

    chunk: str
    done: bool
    status: Optional[str] = None  # Status message: thinking, searching, generating
    sources: List[Any] = []  # List of ChatMessageSource
    tools: List[Any] = []  # List of ChatMessageToolCall
    id: Optional[str] = None
    response: Optional[str] = None  # Full response at the end


# ============================================================================
# API Request/Response Types
# ============================================================================


class ChatCreateRequest(BaseModel):
    """Request model for creating a new chat."""

    project_id: str = Field(description="ID of the project this chat belongs to")


class ChatUpdateRequest(BaseModel):
    """Request model for updating a chat."""

    title: Optional[str] = Field(None, description="Title of the chat")


class SourceDto(BaseModel):
    """Response model for source document data."""

    model_config = {"from_attributes": True}

    id: str = Field(description="Unique ID of the source segment")
    citation_index: int = Field(description="Citation number for [n] references")
    content: str = Field(description="Content of the source segment")
    title: str = Field(description="Title/name of the source document")
    document_id: str = Field(description="ID of the source document")
    preview_url: Optional[str] = Field(
        None, description="URL to preview/download the document"
    )
    score: float = Field(description="Relevance score of the source")


class ToolCallDto(BaseModel):
    """Response model for tool call data."""

    model_config = {"from_attributes": True}

    id: str = Field(description="Unique ID of the tool call")
    type: str = Field(description="Tool type identifier")
    name: str = Field(description="Name of the tool being called")
    state: Literal[
        "input-streaming", "input-available", "output-available", "output-error"
    ] = Field(description="Current state of the tool call")
    input: Optional[Dict[str, Any]] = Field(
        None, description="Input parameters for the tool"
    )
    output: Optional[Dict[str, Any] | str] = Field(
        None, description="Output result from the tool"
    )
    error_text: Optional[str] = Field(None, description="Error message if failed")


class ChatMessageDto(BaseModel):
    """Response model for chat message data."""

    model_config = {"from_attributes": True}

    id: str = Field(description="Unique ID of the message")
    role: str = Field(description="Role of the message sender")
    content: str = Field(description="Content of the message")
    sources: Optional[List[SourceDto]] = Field(
        default=None, description="Source documents for assistant messages"
    )
    tools: Optional[List[ToolCallDto]] = Field(
        default=None, description="Tool calls made during message generation"
    )
    created_at: datetime = Field(description="Creation timestamp")


class LastChatMessageDto(BaseModel):
    """Response model for last chat message data."""

    model_config = {"from_attributes": True}

    id: str = Field(description="Unique ID of the message")
    role: str = Field(description="Role of the message sender")
    content: str = Field(description="Content of the message")
    created_at: datetime = Field(description="Creation timestamp")


class ChatDto(BaseModel):
    """Response model for chat data."""

    model_config = {"from_attributes": True}

    id: str = Field(description="Unique ID of the chat")
    project_id: str = Field(description="ID of the project this chat belongs to")
    user_id: str = Field(description="ID of the user who created the chat")
    title: Optional[str] = Field(description="Title of the chat")
    messages: List[ChatMessageDto] = Field(
        default_factory=list, description="List of messages in the chat"
    )
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")

    last_message: Optional[LastChatMessageDto] = Field(
        default=None, description="Last message in the chat"
    )


class ChatListResponse(BaseModel):
    """Response model for listing chats."""

    data: List[ChatDto] = Field(description="List of chats")


class ChatCompletionRequest(BaseModel):
    """Request model for chat completion with RAG."""

    message: str = Field(description="User message to process")


class StreamingChatMessage(BaseModel):
    """Response model for streaming chat message chunks."""

    model_config = {"from_attributes": True}

    id: str = Field(description="Unique ID of the message")
    chunk: str = Field(description="Text chunk of the response")
    done: bool = Field(description="Whether this is the final chunk")
    status: Optional[str] = Field(
        default=None, description="Status message: thinking, searching, generating"
    )
    sources: Optional[List[SourceDto]] = Field(
        default=None, description="Source documents (only included in final chunk)"
    )
    tools: Optional[List[ToolCallDto]] = Field(
        default=None, description="Tool calls (streamed as they happen)"
    )
