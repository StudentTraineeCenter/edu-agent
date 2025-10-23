from typing import AsyncGenerator, List

from api.dependencies import get_chat_service, get_user
from core.logger import get_logger
from core.services.chat import ChatService
from db.models import User
from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import StreamingResponse
from schemas.chat import (
    ChatCompletionRequest,
    ChatCreateRequest,
    ChatDto,
    ChatListResponse,
    ChatMessageDto,
    ChatUpdateRequest,
    SourceDto,
    StreamingChatMessage,
    ToolCallDto,
)

logger = get_logger(__name__)

router = APIRouter()


@router.post(
    path="",
    response_model=ChatDto,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new chat",
    description="Create a new project",
)
def create_chat(
    body: ChatCreateRequest,
    chat_service: ChatService = Depends(get_chat_service),
    current_user: User = Depends(get_user),
):
    """Create a new chat"""
    logger.info("creating chat")

    result = chat_service.create_chat(body.project_id, current_user.id, None)

    # Format messages with sources
    formatted_messages = []
    for msg in result.messages:
        message_data = {"role": msg["role"], "content": msg["content"]}
        if msg["role"] == "assistant" and "sources" in msg:
            message_data["sources"] = [SourceDto(**source) for source in msg["sources"]]
        if msg["role"] == "assistant" and "tools" in msg:
            message_data["tools"] = [ToolCallDto(**tool) for tool in msg["tools"]]
        formatted_messages.append(ChatMessageDto(**message_data))

    return ChatDto(
        id=result.id,
        project_id=result.project_id,
        user_id=result.user_id,
        title=result.title,
        messages=formatted_messages,
        created_at=result.created_at,
        updated_at=result.updated_at,
    )


@router.get(
    path="",
    response_model=ChatListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all chats",
    description="List all chats",
)
def list_chats(
    project_id: str,
    chat_service: ChatService = Depends(get_chat_service),
    current_user: User = Depends(get_user),
):
    """List all chats"""
    logger.info("listing chats for project_id=%s", project_id)

    result = chat_service.list_chats(project_id, current_user.id)

    # Format messages for each chat
    formatted_chats = []
    for chat in result:
        formatted_messages = []
        for msg in chat.messages:
            message_data = {
                "role": msg["role"],
                "content": msg["content"],
                "id": msg["id"],
            }
            if msg["role"] == "assistant" and "sources" in msg:
                message_data["sources"] = [
                    SourceDto(**source) for source in msg["sources"]
                ]
            if msg["role"] == "assistant" and "tools" in msg:
                message_data["tools"] = [ToolCallDto(**tool) for tool in msg["tools"]]
            formatted_messages.append(ChatMessageDto(**message_data))

        formatted_chats.append(
            ChatDto(
                id=chat.id,
                project_id=chat.project_id,
                user_id=chat.user_id,
                title=chat.title,
                messages=formatted_messages,
                created_at=chat.created_at,
                updated_at=chat.updated_at,
            )
        )

    return ChatListResponse(
        data=formatted_chats,
        total_count=len(result),
    )


@router.get(
    path="/{chat_id}",
    response_model=ChatDto,
    status_code=status.HTTP_200_OK,
    summary="Get a chat by id",
    description="Get a chat by id",
)
def get_chat(
    chat_id: str,
    chat_service: ChatService = Depends(get_chat_service),
    current_user: User = Depends(get_user),
):
    """Get a chat by id"""

    logger.info("getting chat_id=%s", chat_id)

    result = chat_service.get_chat(chat_id, current_user.id)

    if not result:
        logger.error("chat_id=%s not found", chat_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found",
        )

    # Format messages with sources
    formatted_messages = []
    for msg in result.messages:
        message_data = {"role": msg["role"], "content": msg["content"], "id": msg["id"]}
        if msg["role"] == "assistant" and "sources" in msg:
            message_data["sources"] = [SourceDto(**source) for source in msg["sources"]]
        if msg["role"] == "assistant" and "tools" in msg:
            message_data["tools"] = [ToolCallDto(**tool) for tool in msg["tools"]]
        formatted_messages.append(ChatMessageDto(**message_data))

    return ChatDto(
        id=result.id,
        project_id=result.project_id,
        user_id=result.user_id,
        title=result.title,
        messages=formatted_messages,
        created_at=result.created_at,
        updated_at=result.updated_at,
    )


@router.put(
    path="/{chat_id}",
    response_model=ChatDto,
    status_code=status.HTTP_200_OK,
    summary="Update a chat by id",
    description="Update a chat by id",
)
def update_chat(
    chat_id: str,
    body: ChatUpdateRequest,
    chat_service: ChatService = Depends(get_chat_service),
    current_user: User = Depends(get_user),
):
    """Update a chat by id"""
    logger.info("updating chat_id=%s", chat_id)

    result = chat_service.update_chat(chat_id, current_user.id, body.title)

    # Format messages with sources
    formatted_messages = []
    for msg in result.messages:
        message_data = {"role": msg["role"], "content": msg["content"], "id": msg["id"]}
        if msg["role"] == "assistant" and "sources" in msg:
            message_data["sources"] = [SourceDto(**source) for source in msg["sources"]]
        if msg["role"] == "assistant" and "tools" in msg:
            message_data["tools"] = [ToolCallDto(**tool) for tool in msg["tools"]]
        formatted_messages.append(ChatMessageDto(**message_data))

    return ChatDto(
        id=result.id,
        project_id=result.project_id,
        user_id=result.user_id,
        title=result.title,
        messages=formatted_messages,
        created_at=result.created_at,
        updated_at=result.updated_at,
    )


@router.post(
    "/{chat_id}/archive",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Archive a chat by id",
    description="Archive a chat by id",
)
def archive_chat(
    chat_id: str,
    chat_service: ChatService = Depends(get_chat_service),
    current_user: User = Depends(get_user),
):
    """Archive a project by id"""
    logger.info("archiving chat_id=%s", chat_id)
    chat_service.archive_chat(chat_id, current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{chat_id}/messages",
    response_model=List[ChatMessageDto],
    status_code=status.HTTP_200_OK,
    summary="List messages in a chat",
    description="List all messages in a chat with sources",
)
def list_chat_messages(
    chat_id: str,
    chat_service: ChatService = Depends(get_chat_service),
    current_user: User = Depends(get_user),
):
    """List all messages in a chat"""
    logger.info("listing messages for chat_id=%s", chat_id)

    chat = chat_service.get_chat(chat_id, current_user.id)
    if not chat:
        logger.error("chat_id=%s not found", chat_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found",
        )

    # Format messages with sources
    formatted_messages = []
    for msg in chat.messages:
        message_data = {"role": msg["role"], "content": msg["content"], "id": msg["id"]}
        if msg["role"] == "assistant" and "sources" in msg:
            message_data["sources"] = [SourceDto(**source) for source in msg["sources"]]
        if msg["role"] == "assistant" and "tools" in msg:
            message_data["tools"] = [ToolCallDto(**tool) for tool in msg["tools"]]
        formatted_messages.append(ChatMessageDto(**message_data))

    return formatted_messages


@router.post(
    "/{chat_id}/messages/stream",
    status_code=status.HTTP_200_OK,
    summary="Send a streaming message to a chat",
    description="Send a message to a chat with streaming response",
)
async def send_streaming_message(
    chat_id: str,
    body: ChatCompletionRequest,
    chat_service: ChatService = Depends(get_chat_service),
    current_user: User = Depends(get_user),
):
    """Send a streaming message to a chat"""

    user_id = current_user.id

    async def generate_stream() -> AsyncGenerator[str, None]:
        """Generate streaming response chunks"""
        try:
            logger.info("starting streaming response generation")
            async for chunk_data in chat_service.send_streaming_message(
                chat_id, user_id, body.message
            ):
                # Format sources if present
                sources_list = None
                if chunk_data.get("sources"):
                    sources_list = [
                        SourceDto(**source) for source in chunk_data["sources"]
                    ]

                # Format tools if present
                tools_list = None
                if chunk_data.get("tools"):
                    tools_list = [ToolCallDto(**tool) for tool in chunk_data["tools"]]

                # Create the streaming message object
                streaming_msg = StreamingChatMessage(
                    chunk=chunk_data.get("chunk", ""),
                    done=chunk_data.get("done", False),
                    sources=sources_list,
                    tools=tools_list,
                    id=chunk_data.get("id", ""),
                )

                message_json = streaming_msg.model_dump_json()
                sse_data = f"data: {message_json}\n\n"
                yield sse_data.encode("utf-8")

        except Exception as e:
            logger.error("error in streaming: %s", e, exc_info=True)
            error_msg = StreamingChatMessage(
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
