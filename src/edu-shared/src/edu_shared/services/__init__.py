"""Services for managing entities."""

from edu_shared.services.chats import ChatService
from edu_shared.services.documents import DocumentService
from edu_shared.exceptions import NotFoundError
from edu_shared.services.flashcard_groups import FlashcardGroupService
from edu_shared.services.mind_maps import MindMapService
from edu_shared.services.notes import NoteService
from edu_shared.services.practice import PracticeService
from edu_shared.services.projects import ProjectService
from edu_shared.services.quizzes import QuizService
from edu_shared.services.search import SearchService
from edu_shared.services.study_sessions import StudySessionService
from edu_shared.services.usage import UsageService
from edu_shared.services.users import UserService
from edu_shared.services.document_processing import DocumentProcessingService

__all__ = [
    "ChatService",
    "DocumentService",
    "DocumentProcessingService",
    "FlashcardGroupService",
    "MindMapService",
    "NoteService",
    "PracticeService",
    "ProjectService",
    "QuizService",
    "SearchService",
    "StudySessionService",
    "UsageService",
    "UserService",
    "NotFoundError",
]

