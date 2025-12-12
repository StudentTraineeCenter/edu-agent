"""Routers for CRUD operations."""

from routers.projects import router as projects_router
from routers.documents import router as documents_router
from routers.chats import router as chats_router
from routers.notes import router as notes_router
from routers.quizzes import router as quizzes_router
from routers.flashcard_groups import router as flashcard_groups_router
from routers.users import router as users_router

__all__ = [
    "projects_router",
    "documents_router",
    "chats_router",
    "notes_router",
    "quizzes_router",
    "flashcard_groups_router",
    "users_router",
]

