"""Routers for CRUD operations."""

from routers.projects import router as projects_router
from routers.documents import router as documents_router
from routers.chats import router as chats_router
from routers.notes import router as notes_router
from routers.quizzes import router as quizzes_router
from routers.flashcard_groups import router as flashcard_groups_router
from routers.practice_records import router as practice_records_router
from routers.mind_maps import router as mind_maps_router
from routers.study_sessions import router as study_sessions_router, router_global as study_sessions_global_router
from routers.usage import router as usage_router
from routers.users import router as users_router
from routers.auth import router as auth_router

__all__ = [
    "projects_router",
    "documents_router",
    "chats_router",
    "notes_router",
    "quizzes_router",
    "flashcard_groups_router",
    "practice_records_router",
    "mind_maps_router",
    "study_sessions_router",
    "study_sessions_global_router",
    "usage_router",
    "users_router",
    "auth_router",
]

