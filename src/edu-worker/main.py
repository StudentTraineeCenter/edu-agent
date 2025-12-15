import asyncio
import base64
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from azure.storage.queue import QueueClient, QueueMessage
from config import get_settings
from edu_core.db.session import init_db
from edu_core.services.search import SearchService
from edu_queue.schemas import QueueTaskMessage
from processors.registry import ProcessorRegistry
from rich.console import Console

console = Console(force_terminal=True)


async def process_message(
    msg: QueueMessage,
    registry: ProcessorRegistry,
):
    """Process a queue message using the appropriate processor.

    Args:
        msg: The queue message to process
        registry: ProcessorRegistry for getting processors
    """
    with console.status("[bold green]Processing message...[/bold green]"):
        # Decode message
        content = json.loads(base64.b64decode(msg.content).decode("utf-8"))

        # Parse using schema (TypedDict for type checking)
        task_message: QueueTaskMessage = content

        task_type = task_message["type"]
        task_data = task_message["data"]

        console.log(
            f"Received task: {task_type} for project: {task_data.get('project_id', 'N/A')}"
        )

        # Get processor for this task type
        processor = registry.get_processor(task_type)

        # Process the task
        await processor.process(task_data)

        console.log(f"Completed task: {task_type}")


def main():
    settings = get_settings()

    # Initialize database connection
    init_db(settings.database_url)

    queue = QueueClient.from_connection_string(
        settings.azure_storage_connection_string, settings.azure_storage_queue_name
    )

    search_service = SearchService(
        database_url=settings.database_url,
        azure_openai_embedding_deployment=settings.azure_openai_embedding_deployment,
        azure_openai_endpoint=settings.azure_openai_endpoint,
        azure_openai_api_version=settings.azure_openai_api_version,
    )

    # Create processor registry
    registry = ProcessorRegistry(
        search_service=search_service,
        azure_openai_chat_deployment=settings.azure_openai_chat_deployment,
        azure_openai_endpoint=settings.azure_openai_endpoint,
        azure_openai_api_version=settings.azure_openai_api_version,
        azure_storage_connection_string=settings.azure_storage_connection_string,
        azure_storage_input_container_name=settings.azure_storage_input_container_name,
        azure_storage_output_container_name=settings.azure_storage_output_container_name,
        azure_cu_endpoint=settings.azure_cu_endpoint,
        azure_cu_key=settings.azure_cu_key,
        azure_cu_analyzer_id=settings.azure_cu_analyzer_id,
        azure_openai_embedding_deployment=settings.azure_openai_embedding_deployment,
    )

    console.print("[bold green]Worker started. Polling queue...[/bold green]")

    def process_in_thread(msg: QueueMessage):
        """Run async process_message in a thread"""
        try:
            asyncio.run(process_message(msg, registry))
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
                futures = {
                    executor.submit(process_in_thread, msg): msg for msg in messages
                }

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
