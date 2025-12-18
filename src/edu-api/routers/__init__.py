from .auth import router as auth_router
from .blob_proxy import router as blob_proxy_router
from .chats import router as chats_router
from .documents import router as documents_router
from .flashcard_groups import router as flashcard_groups_router
from .mind_maps import router as mind_maps_router
from .notes import router as notes_router
from .practice_records import router as practice_records_router
from .projects import router as projects_router
from .quizzes import router as quizzes_router
from .study_sessions import (
    router as study_sessions_router,
)
from .study_sessions import (
    router_global as study_sessions_global_router,
)
from .usage import router as usage_router
from .users import router as users_router

__all__ = [
    "auth_router",
    "blob_proxy_router",
    "chats_router",
    "documents_router",
    "flashcard_groups_router",
    "mind_maps_router",
    "notes_router",
    "practice_records_router",
    "projects_router",
    "quizzes_router",
    "study_sessions_global_router",
    "study_sessions_router",
    "usage_router",
    "users_router",
]
