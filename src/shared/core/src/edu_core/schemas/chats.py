from datetime import datetime
from typing import Any, Literal, Union

from pydantic import BaseModel, Field


class ChatMessagePartDto(BaseModel):
    model_config = {"from_attributes": True}
    id: str | None = Field(
        None, description="Unique ID of the part (for streaming tracking)"
    )
    order: int = Field(default=0, description="Order of the part within the message")


class TextPartDto(ChatMessagePartDto):
    type: Literal["text"] = "text"
    text_content: str = Field(..., description="Text content of the message part")


class FilePartDto(ChatMessagePartDto):
    type: Literal["file"] = "file"
    file_name: str = Field(..., description="Original name of the uploaded file")
    file_type: str = Field(..., description="MIME type of the uploaded file")
    file_url: str = Field(..., description="URL to access the uploaded file")


class ToolCallPartDto(ChatMessagePartDto):
    type: Literal["tool_call"] = "tool_call"
    tool_call_id: str = Field(..., description="Unique ID of the tool call")
    tool_name: str = Field(..., description="Name of the tool being called")
    tool_input: dict[str, Any] | None = Field(
        None, description="Input parameters for the tool"
    )
    tool_output: dict[str, Any] | str | None = Field(
        None, description="Output result from the tool"
    )
    tool_state: Literal[
        "input-streaming", "input-available", "output-available", "output-error"
    ] = Field(..., description="Current state of the tool call")


class SourceDocumentPartDto(ChatMessagePartDto):
    type: Literal["source-document"] = "source-document"
    source_id: str = Field(..., description="Unique identifier for the source document")
    media_type: str = Field(..., description="MIME type of the source document")
    title: str = Field(..., description="Title of the source document")
    filename: str | None = Field(None, description="Filename of the source document")
    provider_metadata: dict[str, Any] | None = Field(
        None, description="Additional metadata from the provider"
    )


class ChatMessageDto(BaseModel):
    model_config = {"from_attributes": True}

    id: str = Field(..., description="Unique ID of the message")
    chat_id: str = Field(..., description="ID of the chat this message belongs to")
    role: str = Field(..., description="Role of the message sender")
    created_at: datetime = Field(
        ..., description="Date and time the message was created"
    )
    parts: list[
        Union[TextPartDto, FilePartDto, ToolCallPartDto, SourceDocumentPartDto]
    ] = Field(default_factory=list, description="List of parts composing the message")


class ChatDto(BaseModel):
    model_config = {"from_attributes": True}

    id: str = Field(..., description="Unique ID of the chat")
    project_id: str = Field(..., description="ID of the project this chat belongs to")
    user_id: str = Field(..., description="ID of the user who created the chat")
    title: str | None = Field(None, description="Title of the chat")
    created_at: datetime = Field(..., description="Date and time the chat was created")
    updated_at: datetime = Field(..., description="Date and time the chat was updated")
    last_message_content: str | None = Field(
        None, description="Content preview of the last message"
    )
    last_message_at: datetime | None = Field(
        None, description="Date and time of the last message"
    )


class ChatDetailDto(ChatDto):
    """Chat DTO with messages and parts included."""

    messages: list[ChatMessageDto] = Field(
        default_factory=list, description="List of messages in the chat"
    )



class StreamingChatMessage(ChatMessageDto):
    """Response model for streaming chat message chunks"""

    done: bool = Field(default=False, description="Whether this is the final chunk")


class StreamEventDto(BaseModel):
    """DTO for a single SSE event in the chat stream."""

    message_id: str = Field(..., description="ID of the message")
    chat_id: str = Field(..., description="ID of the chat")
    role: str = Field(..., description="Role of the sender")
    created_at: datetime | str = Field(..., description="Creation timestamp")
    done: bool = Field(..., description="Whether the stream is done")
    part_id: str | None = Field(
        None, description="ID of the part (streaming text chunks)"
    )
    delta: str | None = Field(None, description="Text delta content")
    part: Union[
        TextPartDto, FilePartDto, ToolCallPartDto, SourceDocumentPartDto, dict[str, Any]
    ] | None = Field(None, description="Complete part object")
    status: str | None = Field(None, description="Status of the generation")
