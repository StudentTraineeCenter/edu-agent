from core.agents.search import DocumentSearchAdapter
from core.auth import get_current_user
from core.services.attempts import AttemptService
from core.services.chat import ChatService
from core.services.data_processing import DataProcessingService
from core.services.documents import DocumentService
from core.services.flashcards import FlashcardService
from core.services.notes import NoteService
from core.services.projects import ProjectService
from core.services.quizzes import QuizService
from core.services.study_plans import StudyPlanService
from core.services.usage import UsageService
from db.models import User
from fastapi import Depends

project_service = ProjectService()
document_service = DocumentService()
data_processing_service = DataProcessingService()

# Create unified search interface - single source of truth
search_interface = DocumentSearchAdapter(document_service)

# Create usage service first
usage_service = UsageService()

# Create services with unified search interface
chat_service = ChatService(
    search_interface=search_interface, usage_service=usage_service
)
flashcard_service = FlashcardService(search_interface=search_interface)
quiz_service = QuizService(search_interface=search_interface)
note_service = NoteService(search_interface=search_interface)
attempt_service = AttemptService()
study_plan_service = StudyPlanService(attempt_service=attempt_service)


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


def get_note_service():
    return note_service


def get_attempt_service():
    return attempt_service


def get_user(current_user: User = Depends(get_current_user)) -> User:
    """Get authenticated user (required)"""
    return current_user


def get_data_processing_service():
    return data_processing_service


def get_usage_service():
    return usage_service


def get_study_plan_service():
    return study_plan_service
