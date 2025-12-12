"""CRUD service for managing chats."""

from contextlib import contextmanager
from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from edu_shared.db.models import Chat
from edu_shared.db.session import get_session_factory
from edu_shared.schemas.chats import ChatDto, ChatMessageDto, SourceDto, ToolCallDto
from edu_shared.exceptions import NotFoundError


class ChatService:
    """Service for managing chats."""

    def __init__(self) -> None:
        """Initialize the chat service."""
        pass

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

