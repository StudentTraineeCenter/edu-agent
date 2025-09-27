from core.service.chat_service import ChatService
from core.service.document_service import DocumentService
from core.service.project_service import ProjectService


document_service = DocumentService()
chat_service = ChatService(document_service=document_service)
project_service = ProjectService()


def get_document_service():
    return document_service


def get_chat_service():
    return chat_service


def get_project_service():
    return project_service
