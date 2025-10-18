import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional, AsyncGenerator, Callable, Awaitable, Tuple
from uuid import uuid4
import xml.etree.ElementTree as ET

from azure.identity import get_bearer_token_provider, DefaultAzureCredential
from langchain_openai import AzureChatOpenAI
from pydantic import BaseModel

from core.config import app_config
from core.logger import get_logger
from db.model import Chat, ChatMessage, ChatMessageSource
from db.session import SessionLocal

logger = get_logger(__name__)


class MessageChunk(BaseModel):
    chunk: str
    done: bool
    sources: List[ChatMessageSource] = []
    id: Optional[str] = None
    response: Optional[str] = None  # Full response at the end


GetRelevantContextType = Callable[
    [str, str, int],  # parameters: query, project_id, top_k
    Awaitable[Tuple[str, List[ChatMessageSource]]]
]

class ChatService:
    def __init__(self, get_relevant_context: GetRelevantContextType):
        self.get_relevant_context = get_relevant_context

        self.credential = DefaultAzureCredential()

        self.token_provider = get_bearer_token_provider(
            self.credential, "https://cognitiveservices.azure.com/.default"
        )

        self.llm_streaming = AzureChatOpenAI(
            azure_deployment=app_config.AZURE_OPENAI_CHAT_DEPLOYMENT,
            azure_endpoint=app_config.AZURE_OPENAI_ENDPOINT,
            api_version="2024-12-01-preview",
            azure_ad_token_provider=self.token_provider,
            temperature=0,
            streaming=True,
        )

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

    def get_chat(self, chat_id: str, user_id: str) -> Optional[Chat]:
        """Get a chat by id"""
        with SessionLocal() as db:
            try:
                chat = (
                    db.query(Chat)
                    .filter(Chat.id == chat_id, Chat.user_id == user_id)
                    .first()
                )
                return chat
            except Exception as e:
                logger.error(f"Error getting chat: {e}")
                raise e

    def list_chats(self, project_id: str, user_id: str) -> List[Chat]:
        """List all chats for a project"""
        with SessionLocal() as db:
            try:
                return (
                    db.query(Chat)
                    .filter(Chat.project_id == project_id, Chat.user_id == user_id)
                    .all()
                )
            except Exception as e:
                logger.error(f"Error listing chats: {e}")
                raise e

    def update_chat(self, chat_id: str, user_id: str, title: Optional[str]) -> Chat:
        """Update a chat"""
        with SessionLocal() as db:
            try:
                chat = (
                    db.query(Chat)
                    .filter(Chat.id == chat_id, Chat.user_id == user_id)
                    .first()
                )
                if not chat:
                    raise ValueError(f"Chat with id {chat_id} not found")

                chat.title = title

                db.commit()
                db.refresh(chat)
                return chat
            except Exception as e:
                logger.error(f"Error updating chat: {e}")
                raise e

    def archive_chat(self, chat_id: str, user_id: str) -> Chat:
        """Archive a chat"""
        with SessionLocal() as db:
            try:
                chat: Optional[Chat] = (
                    db.query(Chat)
                    .filter(Chat.id == chat_id, Chat.user_id == user_id)
                    .first()
                )
                if not chat:
                    raise ValueError(f"chat_id={chat_id} not found")

                chat.archived_at = datetime.now()

                db.commit()
                db.refresh(chat)
                return chat
            except Exception as e:
                logger.error(f"Error archiving chat: {e}")
                raise e

    async def send_streaming_message(
        self, chat_id: str, user_id: str, message: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Send a streaming message to a chat using grounded RAG responses"""
        with SessionLocal() as db:
            try:
                chat: Optional[Chat] = (
                    db.query(Chat)
                    .filter(Chat.id == chat_id, Chat.user_id == user_id)
                    .first()
                )
                if not chat:
                    raise ValueError(f"Chat with id {chat_id} not found")

                messages: list[ChatMessage] = [
                    ChatMessage(**msg) for msg in chat.messages
                ]

                # Generate message IDs upfront
                user_message_id = str(uuid4())
                assistant_message_id = str(uuid4())

                # Context
                (
                    relevant_context,
                    sources,
                ) = await self.get_relevant_context(message, chat.project_id, 5)

                # Stream the response
                async for chunk_data in self._get_response_stream(
                    query=message,
                    messages=messages,
                    context=relevant_context,
                    language_code=chat.project.language_code,
                    sources=sources,
                ):
                    # If this is the final chunk, save the complete message to database
                    if (chunk_data.done or False) and hasattr(chunk_data, "response"):
                        response = chunk_data.response
                        sources = chunk_data.sources or []
                        if len(sources) > 0:
                            # Convert sources to dicts
                            sources = [s.model_dump() for s in sources]

                        new_messages = chat.messages + [
                            {"role": "user", "content": message, "id": user_message_id},
                            {
                                "id": assistant_message_id,
                                "role": "assistant",
                                "content": response,
                                "sources": sources,
                            },
                        ]

                        chat.messages = new_messages
                        chat.updated_at = datetime.now()
                        db.commit()

                        # Return the final chunk with message_id
                        yield {
                            "chunk": chunk_data.chunk or "",
                            "done": True,
                            "sources": sources,
                            "chat_id": chat_id,
                            "id": assistant_message_id,
                        }
                    else:
                        # Return streaming chunk with message_id
                        yield {
                            **chunk_data.model_dump(),
                            "chat_id": chat_id,
                            "id": assistant_message_id,
                        }

            except Exception as e:
                logger.error(f"Error sending streaming message: {e}")
                yield {
                    "chunk": f"Error: {str(e)}",
                    "done": True,
                    "sources": [],
                    "id": "",
                }

    async def _get_response_stream(
        self,
        query: str,
        messages: list[ChatMessage],
        context: str,
        language_code: str,
        sources: list[ChatMessageSource],
    ) -> AsyncGenerator[MessageChunk, None]:
        chat_history = self._build_chat_history_context(messages)

        prompt_template = f"""You are a helpful AI assistant that answers questions based on the provided documents.

            CITATION INSTRUCTIONS:
            - When using information from the context below, cite the source using [n] where n is the document number
            - Place citations immediately after the relevant statement or claim
            - Example: "The study found that students learn better with active recall [1] while spaced repetition improves retention [2]."
            - If you don't know the answer or the context doesn't contain relevant information, say so clearly

            IMPORTANT: Respond in {language_code} language. All your responses must be in {language_code}.

            {chat_history}

            Context:
            {context}

            Question: {query}
            Answer:"""

        accumulated_response = ""

        async for chunk in self.llm_streaming.astream(prompt_template):
            if chunk.content:
                chunk_text = chunk.content
                accumulated_response += chunk_text

                yield MessageChunk(chunk=chunk_text, done=False)

                # Small delay to prevent socket buffer overflow
                await asyncio.sleep(0.001)

        yield MessageChunk(
            chunk="",
            done=True,
            sources=sources,
            response=accumulated_response,
        )

    @staticmethod
    def _build_chat_history_context(
        chat_history: list[ChatMessage],
        n: int = 6,
    ) -> str:
        """Build context string from chat history."""
        """Build XML context string from chat history (last 6 messages)."""
        root = ET.Element("previous_conversation")
        for i, msg in enumerate(chat_history[-n:], start=1):
            el = ET.Element("message", index=str(i))
            role_el = ET.SubElement(el, "role")
            role_el.text = "User" if msg.role == "user" else "Assistant"
            content_el = ET.SubElement(el, "content")
            content_el.text = msg.content
            root.append(el)
        return ET.tostring(root, encoding="unicode")
