from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from core.logger import get_logger
from core.service.document_service import DocumentService

from db.model import Chat
from db.session import SessionLocal

logger = get_logger(__name__)


class ChatService:
    def __init__(self, document_service: DocumentService):
        self.document_service = document_service

    def create_chat(self, project_id: str, user_id: str, title: Optional[str]) -> Chat:
        """Create a new chat"""

        with SessionLocal() as db:
            chat = Chat(
                id=str(uuid4()),
                project_id=project_id,
                user_id=user_id,
                title=title,
                messages=[],
                created_at=datetime.now(),
                updated_at=datetime.now(),
                archived_at=None,
            )
            if not title:
                chat.title = f"Chat {chat.id[:8]}"
            db.add(chat)
            db.commit()
            db.refresh(chat)
            logger.info(f"Chat created: {chat.id}")
            return chat

    def get_chat(self, chat_id: str) -> Optional[Chat]:
        """Get a chat by id"""
        with SessionLocal() as db:
            try:
                chat = db.query(Chat).filter(Chat.id == chat_id).first()
                return chat
            except Exception as e:
                logger.error(f"Error getting chat: {e}")
                raise e

    def list_chats(self, project_id: str) -> List[Chat]:
        """List all chats for a project"""
        with SessionLocal() as db:
            try:
                return db.query(Chat).filter(Chat.project_id == project_id).all()
            except Exception as e:
                logger.error(f"Error listing chats: {e}")
                raise e

    def update_chat(self, chat_id: str, title: Optional[str]) -> Chat:
        """Update a chat"""
        with SessionLocal() as db:
            try:
                chat = db.query(Chat).filter(Chat.id == chat_id).first()
                if not chat:
                    raise ValueError(f"Chat with id {chat_id} not found")

                chat.title = title

                db.commit()
                db.refresh(chat)
                return chat
            except Exception as e:
                logger.error(f"Error updating chat: {e}")
                raise e

    def archive_chat(self, chat_id: str) -> Chat:
        """Archive a chat"""
        with SessionLocal() as db:
            try:
                chat = db.query(Chat).filter(Chat.id == chat_id).first()
                if not chat:
                    raise ValueError(f"Chat with id {chat_id} not found")

                chat.archived_at = datetime.now()

                db.commit()
                db.refresh(chat)
                return chat
            except Exception as e:
                logger.error(f"Error archiving chat: {e}")
                raise e

    async def send_message(self, chat_id: str, message: str):
        """Send a message to a chat using grounded RAG responses"""
        with SessionLocal() as db:
            try:
                chat = db.query(Chat).filter(Chat.id == chat_id).first()
                if not chat:
                    raise ValueError(f"Chat with id {chat_id} not found")

                # Use the new grounded response method with chat history
                grounded_result = await self.document_service.get_grounded_response(
                    query=message,
                    project_id=chat.project_id,
                    top_k=5,
                    chat_history=chat.messages,
                )

                response = grounded_result["response"]
                sources = grounded_result["sources"]

                new_messages = chat.messages + [
                    {"role": "user", "content": message},
                    {"role": "assistant", "content": response, "sources": sources},
                ]

                chat.messages = new_messages
                chat.updated_at = datetime.now()
                db.commit()

                return {
                    "response": response,
                    "sources": sources,
                    "chat_id": chat_id,
                }
            except Exception as e:
                logger.error(f"Error sending message: {e}")
                raise e
