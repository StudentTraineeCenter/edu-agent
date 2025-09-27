from fastapi import APIRouter

from api.v1.project.endpoint import router as projects_router
from api.v1.chat.endpoint import router as chats_router
from api.v1.document.endpoint import router as documents_router


v1_router = APIRouter()

v1_router.include_router(router=projects_router, prefix="/projects", tags=["projects"])
v1_router.include_router(router=chats_router, prefix="/chats", tags=["chats"])
v1_router.include_router(
    router=documents_router, prefix="/documents", tags=["documents"]
)
