"""Services for managing entities."""

from edu_shared.services.chats import ChatService
from edu_shared.services.documents import DocumentService
from edu_shared.exceptions import NotFoundError
from edu_shared.services.flashcard_groups import FlashcardGroupService
from edu_shared.services.notes import NoteService
from edu_shared.services.projects import ProjectService
from edu_shared.services.quizzes import QuizService
from edu_shared.services.search import SearchService
from edu_shared.services.users import UserService

__all__ = [
    "ChatService",
    "DocumentService",
    "FlashcardGroupService",
    "NoteService",
    "ProjectService",
    "QuizService",
    "SearchService",
    "UserService",
    "NotFoundError",
]

