import asyncio
import base64
import json
import time

from azure.storage.queue import QueueClient, QueueMessage
from rich.console import Console

from edu_shared.agents.flashcard_agent import FlashcardAgent
from edu_shared.agents.quiz_agent import QuizAgent
from edu_shared.agents.note_agent import NoteAgent
from edu_shared.agents.base import ContentAgentConfig
from edu_shared.schemas.queue import QueueTaskMessage, TaskType, FlashcardGenerationData
from edu_shared.services.search import SearchService
from edu_shared.db.session import init_db

from config import get_settings

console = Console(force_terminal=True)


async def process_message(msg: QueueMessage, search_service: SearchService, config: ContentAgentConfig):
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
                custom_instructions=flashcard_data.get("custom_instructions")
            )

        if task_type == TaskType.QUIZ_GENERATION:
            quiz_agent = QuizAgent(config=config, search_service=search_service)
    
        if task_type == TaskType.NOTE_GENERATION:
            note_agent = NoteAgent(config=config, search_service=search_service)

        console.log(f"Completed task: {task_type}")


async def main():
    settings = get_settings()

    # Initialize database connection
    init_db(settings.database_url)

    queue = QueueClient.from_connection_string(
        settings.azure_storage_connection_string, settings.azure_storage_queue_name
    )

    config = ContentAgentConfig(
        azure_openai_chat_deployment=settings.azure_openai_chat_deployment,
        azure_openai_endpoint=settings.azure_openai_endpoint,
        azure_openai_api_version=settings.azure_openai_api_version
    )

    search_service = SearchService(
        database_url=settings.database_url,
        azure_openai_embedding_deployment=settings.azure_openai_embedding_deployment,
        azure_openai_endpoint=settings.azure_openai_endpoint,
        azure_openai_api_version=settings.azure_openai_api_version
    )

    console.print("[bold green]Worker started. Polling queue...[/bold green]")

    while True:
        # Get messages (visibility_timeout hides it from other workers for 5 mins)
        messages = queue.receive_messages(visibility_timeout=300, max_messages=5)
        for msg in messages:
            try:
                await process_message(msg, search_service, config)
                queue.delete_message(msg)  # Done!
            except Exception as e:
                print(f"Error: {e}")
                # Message reappears after timeout (retry mechanism)

        time.sleep(1)  # Prevent tight loop


if __name__ == "__main__":
    asyncio.run(main())
