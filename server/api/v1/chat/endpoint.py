from fastapi import APIRouter, status, HTTPException, Response, Depends
from typing import List

from api.v1.chat.schema import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCreateRequest,
    ChatDto,
    ChatMessageDto,
    ChatUpdateRequest,
    ChatListResponse,
    SourceDto,
)
from api.v1.deps import get_chat_service

from core.logger import get_logger

from core.service.chat_service import ChatService

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
):
    """Create a new chat"""
    logger.info(f"Creating chat")

    result = chat_service.create_chat(body.project_id, body.user_id, None)

    return ChatDto.from_orm_with_messages(result)


@router.get(
    path="",
    response_model=ChatListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all chats",
    description="List all chats",
)
def list_chats(project_id: str, chat_service: ChatService = Depends(get_chat_service)):
    """List all chats"""
    logger.info(f"Listing chats for project: {project_id}")

    result = chat_service.list_chats(project_id)

    return ChatListResponse(
        data=[ChatDto.from_orm_with_messages(chat) for chat in result],
        total_count=len(result),
    )


@router.get(
    path="/{chat_id}",
    response_model=ChatDto,
    status_code=status.HTTP_200_OK,
    summary="Get a chat by id",
    description="Get a chat by id",
)
def get_chat(chat_id: str, chat_service: ChatService = Depends(get_chat_service)):
    """Get a chat by id"""

    logger.info(f"Getting chat: {chat_id}")

    result = chat_service.get_chat(chat_id)

    if not result:
        logger.error(f"Chat not found: {chat_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found",
        )

    return ChatDto.from_orm_with_messages(result)


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
):
    """Update a chat by id"""
    logger.info(f"Updating chat: {chat_id}")

    result = chat_service.update_chat(chat_id, body.title)
    return ChatDto.from_orm_with_messages(result)


@router.post(
    "/{chat_id}/archive",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Archive a chat by id",
    description="Archive a chat by id",
)
def archive_chat(chat_id: str, chat_service: ChatService = Depends(get_chat_service)):
    """Archive a project by id"""
    logger.info(f"Archiving chat: {chat_id}")
    chat_service.archive_chat(chat_id)
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
):
    """List all messages in a chat"""
    logger.info(f"Listing messages for chat: {chat_id}")

    chat = chat_service.get_chat(chat_id)
    if not chat:
        logger.error(f"Chat not found: {chat_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found",
        )

    # Format messages with sources
    formatted_messages = []
    for msg in chat.messages:
        message_data = {"role": msg["role"], "content": msg["content"]}
        if msg["role"] == "assistant" and "sources" in msg:
            message_data["sources"] = [SourceDto(**source) for source in msg["sources"]]
        formatted_messages.append(ChatMessageDto(**message_data))

    return formatted_messages


@router.post(
    "/{chat_id}/messages",
    response_model=ChatCompletionResponse,
    status_code=status.HTTP_200_OK,
    summary="Send a message to a chat",
    description="Send a message to a chat",
)
async def send_message(
    chat_id: str,
    body: ChatCompletionRequest,
    chat_service: ChatService = Depends(get_chat_service),
):
    """Send a message to a chat"""
    logger.info(f"Sending message to chat: {chat_id}")

    result = await chat_service.send_message(chat_id, body.message)

    # Format sources for response
    formatted_sources = [SourceDto(**source) for source in result["sources"]]

    return ChatCompletionResponse(
        response=result["response"],
        sources=formatted_sources,
        chat_id=result["chat_id"],
    )
