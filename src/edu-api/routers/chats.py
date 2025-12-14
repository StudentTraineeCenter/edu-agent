"""Router for chat CRUD operations."""

from typing import AsyncGenerator
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse

from auth import get_current_user
from dependencies import get_chat_service, get_chat_service_with_streaming, get_usage_service
from edu_shared.services import ChatService, NotFoundError, UsageService
from edu_shared.schemas.chats import ChatDto, StreamingChatMessage, SourceDto, ToolCallDto
from edu_shared.schemas.users import UserDto
from routers.schemas import ChatCreate, ChatUpdate, ChatCompletionRequest

router = APIRouter(prefix="/api/v1/projects/{project_id}/chats", tags=["chats"])


@router.post("", response_model=ChatDto, status_code=201)
async def create_chat(
    project_id: str,
    chat: ChatCreate,
    current_user: UserDto = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
):
    """Create a new chat."""
    try:
        return service.create_chat(
            project_id=project_id,
            user_id=current_user.id,
            title=chat.title,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{chat_id}", response_model=ChatDto)
async def get_chat(
    project_id: str,
    chat_id: str,
    current_user: UserDto = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
):
    """Get a chat by ID."""
    try:
        return service.get_chat(chat_id=chat_id, user_id=current_user.id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=list[ChatDto])
async def list_chats(
    project_id: str,
    current_user: UserDto = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
):
    """List all chats for a project."""
    try:
        return service.list_chats(project_id=project_id, user_id=current_user.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{chat_id}", response_model=ChatDto)
async def update_chat(
    project_id: str,
    chat_id: str,
    chat: ChatUpdate,
    current_user: UserDto = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
):
    """Update a chat."""
    try:
        return service.update_chat(
            chat_id=chat_id,
            user_id=current_user.id,
            title=chat.title,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{chat_id}", status_code=204)
async def delete_chat(
    project_id: str,
    chat_id: str,
    current_user: UserDto = Depends(get_current_user),
    service: ChatService = Depends(get_chat_service),
):
    """Delete a chat."""
    try:
        service.delete_chat(chat_id=chat_id, user_id=current_user.id)
        return None
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/{chat_id}/messages/stream",
    status_code=200,
    summary="Send a streaming message to a chat",
    description="Send a message to a chat with streaming response",
)
async def send_streaming_message(
    project_id: str,
    chat_id: str,
    body: ChatCompletionRequest,
    current_user: UserDto = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service_with_streaming),
    usage_service: UsageService = Depends(get_usage_service),
):
    """Send a streaming message to a chat."""
    user_id = current_user.id

    # Check usage limit before processing
    usage_service.check_and_increment(user_id, "chat_message")

    async def generate_stream() -> AsyncGenerator[bytes, None]:
        """Generate streaming response chunks"""
        try:
            async for chunk_data in chat_service.send_streaming_message(
                chat_id, user_id, body.message
            ):
                # Format sources if present
                sources_list = None
                if chunk_data.sources:
                    sources_list = [
                        SourceDto(
                            id=source.id,
                            content=source.content,
                            title=source.title,
                            document_id=source.document_id,
                        )
                        for source in chunk_data.sources
                    ]

                # Format tools if present
                tools_list = None
                if chunk_data.tools:
                    tools_list = [
                        ToolCallDto(
                            id=tool.id,
                            type=tool.type,
                            name=tool.name,
                            state=tool.state,
                            input=tool.input,
                            output=tool.output,
                            error_text=tool.error_text,
                        )
                        for tool in chunk_data.tools
                    ]

                # Create the streaming message object
                streaming_msg = StreamingChatMessage(
                    chunk=chunk_data.chunk or "",
                    done=chunk_data.done,
                    status=chunk_data.status,
                    sources=sources_list,
                    tools=tools_list,
                    id=chunk_data.id or "",
                )

                message_json = streaming_msg.model_dump_json()
                sse_data = f"data: {message_json}\n\n"
                yield sse_data.encode("utf-8")

        except Exception as e:
            error_msg = StreamingChatMessage(
                id=str(uuid4()),
                chunk=f"Error: {str(e)}",
                done=True,
                sources=None,
                tools=None,
            )
            yield f"data: {error_msg.model_dump_json()}\n\n".encode("utf-8")

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        },
    )

