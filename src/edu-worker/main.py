import asyncio
import base64
import json
import time

from azure.storage.blob import BlobServiceClient
from azure.storage.queue import QueueClient, QueueMessage
from rich.console import Console

from edu_shared.agents.flashcard_agent import FlashcardAgent
from edu_shared.agents.quiz_agent import QuizAgent
from edu_shared.agents.note_agent import NoteAgent
from edu_shared.agents.base import ContentAgentConfig
from edu_shared.schemas.queue import (
    QueueTaskMessage,
    TaskType,
    FlashcardGenerationData,
    DocumentProcessingData,
)
from edu_shared.services.search import SearchService
from edu_shared.services.document_processing import DocumentProcessingService
from edu_shared.db.session import init_db

from config import get_settings

console = Console(force_terminal=True)


async def process_message(
    msg: QueueMessage,
    search_service: SearchService,
    config: ContentAgentConfig,
    processing_service: DocumentProcessingService,
    blob_service_client: BlobServiceClient,
):
    with console.status("[bold green]Processing message...[/bold green]"):
        # Decode message
        content = json.loads(base64.b64decode(msg.content).decode("utf-8"))

        # Parse using schema (TypedDict for type checking)
        task_message: QueueTaskMessage = content

        task_type = task_message["type"]
        task_data = task_message["data"]

        console.log(f"Received task: {task_type} for project: {task_data['project_id']}")

        if task_type == TaskType.FLASHCARD_GENERATION:
            flashcard_data = FlashcardGenerationData(**task_data)
            flashcard_agent = FlashcardAgent(config=config, search_service=search_service)

            result = await flashcard_agent.generate(
                project_id=flashcard_data["project_id"],
                topic=flashcard_data.get("topic", ""),
                custom_instructions=flashcard_data.get("custom_instructions"),
            )

        if task_type == TaskType.QUIZ_GENERATION:
            quiz_agent = QuizAgent(config=config, search_service=search_service)

        if task_type == TaskType.NOTE_GENERATION:
            note_agent = NoteAgent(config=config, search_service=search_service)

        if task_type == TaskType.DOCUMENT_PROCESSING:
            doc_data = DocumentProcessingData(**task_data)
            document_id = doc_data["document_id"]
            project_id = doc_data["project_id"]

            # Get file content from blob storage
            # First, get document to find blob name
            from edu_shared.db.models import Document
            from edu_shared.db.session import get_session_factory

            SessionLocal = get_session_factory()
            db = SessionLocal()
            try:
                document = db.query(Document).filter(Document.id == document_id).first()
                if not document:
                    raise ValueError(f"Document {document_id} not found")

                # Get blob from input container
                file_extension = (
                    document.file_type if document.file_type != "unknown" else ""
                )
                if file_extension:
                    blob_name = f"{project_id}/{document_id}.{file_extension}"
                else:
                    blob_name = f"{project_id}/{document_id}"

                blob_client = blob_service_client.get_blob_client(
                    container=processing_service.input_container, blob=blob_name
                )
                file_content = blob_client.download_blob().readall()

                # Process document
                await processing_service.process_document(
                    document_id=document_id,
                    file_content=file_content,
                    project_id=project_id,
                )
            finally:
                db.close()

        console.log(f"Completed task: {task_type}")


async def main():
    settings = get_settings()

    # Initialize database connection
    init_db(settings.database_url)

    queue = QueueClient.from_connection_string(
        settings.azure_storage_connection_string, settings.azure_storage_queue_name
    )

    blob_service_client = BlobServiceClient.from_connection_string(
        settings.azure_storage_connection_string
    )

    config = ContentAgentConfig(
        azure_openai_chat_deployment=settings.azure_openai_chat_deployment,
        azure_openai_endpoint=settings.azure_openai_endpoint,
        azure_openai_api_version=settings.azure_openai_api_version,
    )

    search_service = SearchService(
        database_url=settings.database_url,
        azure_openai_embedding_deployment=settings.azure_openai_embedding_deployment,
        azure_openai_endpoint=settings.azure_openai_endpoint,
        azure_openai_api_version=settings.azure_openai_api_version,
    )

    processing_service = DocumentProcessingService(
        database_url=settings.database_url,
        azure_storage_connection_string=settings.azure_storage_connection_string,
        azure_storage_input_container_name=settings.azure_storage_input_container_name,
        azure_storage_output_container_name=settings.azure_storage_output_container_name,
        azure_cu_endpoint=settings.azure_cu_endpoint,
        azure_cu_key=settings.azure_cu_key,
        azure_cu_analyzer_id=settings.azure_cu_analyzer_id,
        azure_openai_embedding_deployment=settings.azure_openai_embedding_deployment,
        azure_openai_endpoint=settings.azure_openai_endpoint,
        azure_openai_api_version=settings.azure_openai_api_version,
    )

    console.print("[bold green]Worker started. Polling queue...[/bold green]")

    while True:
        # Get messages (visibility_timeout hides it from other workers for 5 mins)
        messages = queue.receive_messages(visibility_timeout=300, max_messages=5)
        for msg in messages:
            try:
                await process_message(
                    msg, search_service, config, processing_service, blob_service_client
                )
                queue.delete_message(msg)  # Done!
            except Exception as e:
                console.print(f"[bold red]Error: {e}[/bold red]")
                # Message reappears after timeout (retry mechanism)

        time.sleep(1)  # Prevent tight loop


if __name__ == "__main__":
    asyncio.run(main())
