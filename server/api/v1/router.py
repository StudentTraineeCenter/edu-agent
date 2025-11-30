from api.v1.endpoints.auth import router as auth_router
from api.v1.endpoints.attempts import router as attempts_router
from api.v1.endpoints.chat import router as chats_router
from api.v1.endpoints.documents import router as documents_router
from api.v1.endpoints.flashcards import router as flashcards_router
from api.v1.endpoints.notes import router as notes_router
from api.v1.endpoints.projects import router as projects_router
from api.v1.endpoints.quizzes import router as quizzes_router
from api.v1.endpoints.study_plans import router as study_plans_router
from api.v1.endpoints.usage import router as usage_router
from fastapi import APIRouter

v1_router = APIRouter()

v1_router.include_router(router=projects_router, prefix="/projects", tags=["projects"])
v1_router.include_router(router=chats_router, prefix="/chats", tags=["chats"])
v1_router.include_router(
    router=documents_router, prefix="/documents", tags=["documents"]
)
v1_router.include_router(
    router=flashcards_router, prefix="/flashcards", tags=["flashcards"]
)
v1_router.include_router(router=quizzes_router, prefix="/quizzes", tags=["quizzes"])
v1_router.include_router(router=notes_router, prefix="/notes", tags=["notes"])
v1_router.include_router(router=attempts_router, prefix="/attempts", tags=["attempts"])
v1_router.include_router(router=auth_router, prefix="/auth", tags=["auth"])
v1_router.include_router(router=usage_router, prefix="/usage", tags=["usage"])
v1_router.include_router(router=study_plans_router, tags=["study-plans"])
