from uuid import uuid4

from config import get_settings
from edu_queue.schemas import (
    FlashcardGenerationData,
    QueueTaskMessage,
    TaskType,
)
from edu_queue.service import QueueService
from rich.console import Console

console = Console(force_terminal=True)


def main():
    settings = get_settings()

    console.print("[bold green]Edu API started[/bold green]")

    queue_svc = QueueService(
        connection_string=settings.azure_storage_connection_string,
        queue_name="ai-generation-tasks",  # Make sure this queue exists in Azure/Azurite
    )

    # Note: group_id is now required - the flashcard group should already exist in the database
    task_data: FlashcardGenerationData = {
        "project_id": str(uuid4()),
        "group_id": str(
            uuid4()
        ),  # This should be an existing group_id from the database
        "user_id": str(uuid4()),
        "topic": "Machine Learning Fundamentals",
        "custom_instructions": "Create flashcards for the topic of Machine Learning Fundamentals",
    }

    task_message: QueueTaskMessage = {
        "type": TaskType.FLASHCARD_GENERATION,
        "data": task_data,
    }

    console.print(f"[bold blue]Sending task payload:[/bold blue] {task_message}")

    queue_svc.send_message(task_message)

    console.print("[bold green]Task message sent to queue successfully![/bold green]")


if __name__ == "__main__":
    main()
