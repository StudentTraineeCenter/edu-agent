from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class SourceDto(BaseModel):
    model_config = {"from_attributes": True}

    id: str = Field(..., description="Unique ID of the source segment")
    content: str = Field(..., description="Content of the source segment")
    title: str = Field(..., description="Title/name of the source document")
    document_id: str = Field(..., description="ID of the source document")


class ToolCallDto(BaseModel):
    model_config = {"from_attributes": True}

    id: str = Field(..., description="Unique ID of the tool call")
    type: str = Field(..., description="Tool type identifier")
    name: str = Field(..., description="Name of the tool being called")
    state: Literal[
        "input-streaming", "input-available", "output-available", "output-error"
    ] = Field(..., description="Current state of the tool call")
    input: dict[str, Any] | None = Field(
        None, description="Input parameters for the tool"
    )
    output: dict[str, Any] | str | None = Field(
        None, description="Output result from the tool"
    )
    error_text: str | None = Field(None, description="Error message if failed")


class ChatMessageDto(BaseModel):
    model_config = {"from_attributes": True}

    id: str = Field(..., description="Unique ID of the message")
    role: str = Field(..., description="Role of the message sender")
    content: str = Field(..., description="Content of the message")
    sources: list[SourceDto] | None = Field(
        default=None, description="Source documents for assistant messages"
    )
    tools: list[ToolCallDto] | None = Field(
        default=None, description="Tool calls made during message generation"
    )
    created_at: datetime = Field(
        ..., description="Date and time the message was created"
    )


class ChatDto(BaseModel):
    model_config = {"from_attributes": True}

    id: str = Field(..., description="Unique ID of the chat")
    project_id: str = Field(..., description="ID of the project this chat belongs to")
    user_id: str = Field(..., description="ID of the user who created the chat")
    title: str | None = Field(None, description="Title of the chat")
    messages: list[ChatMessageDto] = Field(
        default_factory=list, description="List of messages in the chat"
    )
    created_at: datetime = Field(..., description="Date and time the chat was created")
    updated_at: datetime = Field(..., description="Date and time the chat was updated")


class StreamingChatMessage(BaseModel):
    """Response model for streaming chat message chunks."""

    model_config = {"from_attributes": True}

    id: str = Field(default="", description="Unique ID of the message")
    chunk: str = Field(default="", description="Text chunk of the response")
    done: bool = Field(default=False, description="Whether this is the final chunk")
    status: str | None = Field(
        default=None, description="Status message: thinking, searching, generating"
    )
    sources: list[SourceDto] | None = Field(
        default=None, description="Source documents (only included in final chunk)"
    )
    tools: list[ToolCallDto] | None = Field(
        default=None, description="Tool calls (streamed as they happen)"
    )
