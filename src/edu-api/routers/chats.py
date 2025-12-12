"""Router for chat CRUD operations."""

from fastapi import APIRouter, HTTPException, Header

from edu_shared.services import ChatService, NotFoundError
from edu_shared.schemas.chats import ChatDto
from routers.schemas import ChatCreate, ChatUpdate

router = APIRouter(prefix="/api/v1/projects/{project_id}/chats", tags=["chats"])


@router.post("", response_model=ChatDto, status_code=201)
async def create_chat(
    project_id: str,
    chat: ChatCreate,
    user_id: str = Header(..., alias="X-User-Id"),
):
    """Create a new chat."""
    service = ChatService()
    try:
        return service.create_chat(
            project_id=project_id,
            user_id=user_id,
            title=chat.title,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{chat_id}", response_model=ChatDto)
async def get_chat(
    project_id: str,
    chat_id: str,
    user_id: str = Header(..., alias="X-User-Id"),
):
    """Get a chat by ID."""
    service = ChatService()
    try:
        return service.get_chat(chat_id=chat_id, user_id=user_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=list[ChatDto])
async def list_chats(
    project_id: str,
    user_id: str = Header(..., alias="X-User-Id"),
):
    """List all chats for a project."""
    service = ChatService()
    try:
        return service.list_chats(project_id=project_id, user_id=user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{chat_id}", response_model=ChatDto)
async def update_chat(
    project_id: str,
    chat_id: str,
    chat: ChatUpdate,
    user_id: str = Header(..., alias="X-User-Id"),
):
    """Update a chat."""
    service = ChatService()
    try:
        return service.update_chat(
            chat_id=chat_id,
            user_id=user_id,
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
    user_id: str = Header(..., alias="X-User-Id"),
):
    """Delete a chat."""
    service = ChatService()
    try:
        service.delete_chat(chat_id=chat_id, user_id=user_id)
        return None
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

