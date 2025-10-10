from fastapi import Depends
from core.service.chat_service import ChatService
from core.service.document_service import DocumentService
from core.service.project_service import ProjectService
from core.service.flashcard_service import FlashcardService
from core.service.quiz_service import QuizService
from core.auth import get_current_user
from db.model import User


document_service = DocumentService()
chat_service = ChatService(document_service=document_service)
project_service = ProjectService()
flashcard_service = FlashcardService()
quiz_service = QuizService()


def get_document_service():
    return document_service


def get_chat_service():
    return chat_service


def get_project_service():
    return project_service


def get_flashcard_service():
    return flashcard_service


def get_quiz_service():
    return quiz_service


def get_user(current_user: User = Depends(get_current_user)) -> User:
    """Get authenticated user (required)"""
    return current_user
