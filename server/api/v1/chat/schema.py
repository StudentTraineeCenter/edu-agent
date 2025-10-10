from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Dict, Any


class ChatCreateRequest(BaseModel):
    """Request model for creating a new chat."""

    project_id: str = Field(description="ID of the project this chat belongs to")


class ChatUpdateRequest(BaseModel):
    """Request model for updating a chat."""

    title: Optional[str] = Field(None, description="Title of the chat")


class SourceDto(BaseModel):
    """Response model for source document data."""

    id: str = Field(description="Unique ID of the source segment")
    content: str = Field(description="Content of the source segment")
    title: str = Field(description="Title/name of the source document")
    document_id: str = Field(description="ID of the source document")
    segment_order: int = Field(description="Order of the segment in the document")
    page_number: Optional[int] = Field(
        None, description="Page number where the content is located"
    )
    preview_url: Optional[str] = Field(
        None, description="URL to preview/download the document"
    )
    score: float = Field(description="Relevance score of the source")


class ChatMessageDto(BaseModel):
    """Response model for chat message data."""

    role: str = Field(description="Role of the message sender")
    content: str = Field(description="Content of the message")
    sources: Optional[List[SourceDto]] = Field(
        default=None, description="Source documents for assistant messages"
    )


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

    @classmethod
    def from_orm_with_messages(cls, chat):
        """Create ChatDto from ORM object with properly formatted messages."""
        formatted_messages = []
        for msg in chat.messages:
            message_data = {"role": msg["role"], "content": msg["content"]}
            if msg["role"] == "assistant" and "sources" in msg:
                message_data["sources"] = [
                    SourceDto(**source) for source in msg["sources"]
                ]
            formatted_messages.append(ChatMessageDto(**message_data))

        return cls(
            id=chat.id,
            project_id=chat.project_id,
            user_id=chat.user_id,
            title=chat.title,
            messages=formatted_messages,
            created_at=chat.created_at,
            updated_at=chat.updated_at,
        )


class ChatListResponse(BaseModel):
    """Response model for listing chats."""

    data: List[ChatDto] = Field(description="List of chats")
    total_count: int = Field(description="Total number of chats")


class ChatCompletionRequest(BaseModel):
    """Request model for chat completion with RAG."""

    message: str = Field(description="User message to process")


class ChatCompletionResponse(BaseModel):
    """Response model for chat completion with RAG."""

    response: str = Field(description="AI assistant response")
    sources: List[SourceDto] = Field(
        description="Source documents used for the response"
    )
    chat_id: str = Field(description="ID of the chat")


class StreamingChatMessage(BaseModel):
    """Response model for streaming chat message chunks."""

    chunk: str = Field(description="Text chunk of the response")
    done: bool = Field(description="Whether this is the final chunk")
    sources: Optional[List[SourceDto]] = Field(
        default=None, description="Source documents (only included in final chunk)"
    )
