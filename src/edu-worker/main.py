import asyncio
import base64
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from azure.storage.blob import BlobServiceClient
from azure.storage.queue import QueueClient, QueueMessage
from config import get_settings
from edu_shared.agents.base import ContentAgentConfig
from edu_shared.db.models import Document
from edu_shared.db.session import get_session_factory, init_db
from edu_shared.schemas.queue import (
    DocumentProcessingData,
    FlashcardGenerationData,
    MindMapGenerationData,
    NoteGenerationData,
    QueueTaskMessage,
    QuizGenerationData,
    TaskType,
)
from edu_shared.services.document_processing import DocumentProcessingService
from edu_shared.services.flashcard_groups import FlashcardGroupService
from edu_shared.services.mind_maps import MindMapService
from edu_shared.services.notes import NoteService
from edu_shared.services.quizzes import QuizService
from edu_shared.services.search import SearchService
from rich.console import Console

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
            service = FlashcardGroupService()

            kwargs = {}
            if flashcard_data.get("count") is not None:
                kwargs["count"] = flashcard_data["count"]
            if flashcard_data.get("difficulty"):
                kwargs["difficulty"] = flashcard_data["difficulty"]

            await service.generate_and_populate(
                group_id=flashcard_data["group_id"],
                project_id=flashcard_data["project_id"],
                search_service=search_service,
                agent_config=config,
                topic=flashcard_data.get("topic"),
                custom_instructions=flashcard_data.get("custom_instructions"),
                **kwargs,
            )
            console.log(f"Populated flashcard group {flashcard_data['group_id']}")

        elif task_type == TaskType.QUIZ_GENERATION:
            quiz_data = QuizGenerationData(**task_data)
            service = QuizService()

            kwargs = {}
            if quiz_data.get("count") is not None:
                kwargs["count"] = quiz_data["count"]

            await service.generate_and_populate(
                quiz_id=quiz_data["quiz_id"],
                project_id=quiz_data["project_id"],
                search_service=search_service,
                agent_config=config,
                topic=quiz_data.get("topic"),
                custom_instructions=quiz_data.get("custom_instructions"),
                **kwargs,
            )
            console.log(f"Populated quiz {quiz_data['quiz_id']}")

        elif task_type == TaskType.NOTE_GENERATION:
            note_data = NoteGenerationData(**task_data)
            service = NoteService()

            result = await service.generate_and_populate(
                note_id=note_data["note_id"],
                project_id=note_data["project_id"],
                search_service=search_service,
                agent_config=config,
                topic=note_data.get("topic"),
                custom_instructions=note_data.get("custom_instructions"),
            )
            console.log(f"Populated note {note_data['note_id']}: {result.title}")

        elif task_type == TaskType.MIND_MAP_GENERATION:
            mind_map_data = MindMapGenerationData(**task_data)
            service = MindMapService()

            if mind_map_data.get("mind_map_id"):
                # Update existing mind map
                result = await service.generate_and_populate(
                    mind_map_id=mind_map_data["mind_map_id"],
                    project_id=mind_map_data["project_id"],
                    user_id=mind_map_data["user_id"],
                    search_service=search_service,
                    agent_config=config,
                    topic=mind_map_data.get("topic"),
                    custom_instructions=mind_map_data.get("custom_instructions"),
                )
                console.log(f"Populated mind map {mind_map_data['mind_map_id']}: {result.title}")
            else:
                # Create new mind map
                result = await service.generate_mind_map(
                    user_id=mind_map_data["user_id"],
                    project_id=mind_map_data["project_id"],
                    search_service=search_service,
                    agent_config=config,
                    topic=mind_map_data.get("topic"),
                    custom_instructions=mind_map_data.get("custom_instructions"),
                )
                console.log(f"Generated new mind map {result.id}: {result.title}")

        elif task_type == TaskType.DOCUMENT_PROCESSING:
            doc_data = DocumentProcessingData(**task_data)
            document_id = doc_data["document_id"]
            project_id = doc_data["project_id"]

            # Get file content from blob storage
            # First, get document to find blob name
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
                console.log(f"Processed document {document_id}")
            finally:
                db.close()
        else:
            raise ValueError(f"Unknown task type: {task_type}")

        console.log(f"Completed task: {task_type}")


def main():
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

    def process_in_thread(msg: QueueMessage):
        """Run async process_message in a thread"""
        try:
            asyncio.run(process_message(
                msg, search_service, config, processing_service, blob_service_client
            ))
            queue.delete_message(msg)  # Done!
        except Exception as e:
            console.print(f"[bold red]Error processing message: {e}[/bold red]")
            # Message reappears after timeout (retry mechanism)

    with ThreadPoolExecutor(max_workers=5) as executor:
        while True:
            # Get messages (visibility_timeout hides it from other workers for 5 mins)
            messages = queue.receive_messages(visibility_timeout=300, max_messages=5)

            if messages:
                # Submit all messages to thread pool
                futures = {executor.submit(process_in_thread, msg): msg for msg in messages}

                # Wait for completion (non-blocking check)
                for future in as_completed(futures):
                    try:
                        future.result()  # This will raise if there was an exception
                    except Exception as e:
                        console.print(f"[bold red]Thread error: {e}[/bold red]")
            else:
                time.sleep(1)  # Prevent tight loop when no messages


if __name__ == "__main__":
    main()
