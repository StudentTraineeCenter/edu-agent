"""Services for managing entities."""

from edu_core.exceptions import NotFoundError
from edu_core.services.chats import ChatService
from edu_core.services.document_upload import DocumentUploadService
from edu_core.services.documents import DocumentService
from edu_core.services.flashcard_groups import FlashcardGroupService
from edu_core.services.mind_maps import MindMapService
from edu_core.services.notes import NoteService
from edu_core.services.practice import PracticeService
from edu_core.services.projects import ProjectService
from edu_core.services.quizzes import QuizService
from edu_core.services.search import SearchService
from edu_core.services.study_plans import StudyPlanService
from edu_core.services.usage import UsageService
from edu_core.services.users import UserService

__all__ = [
    "ChatService",
    "DocumentService",
    "DocumentUploadService",
    "FlashcardGroupService",
    "MindMapService",
    "NotFoundError",
    "NoteService",
    "PracticeService",
    "ProjectService",
    "QuizService",
    "SearchService",
    "SearchService",
    "StudyPlanService",
    "UsageService",
    "UserService",
]
