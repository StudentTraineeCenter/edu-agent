from uuid import uuid4

from rich.console import Console

from config import get_settings
from services.queue import QueueService

console = Console(force_terminal=True)


def main():
    settings = get_settings()

    console.print("[bold green]Edu API started[/bold green]")

    queue_svc = QueueService(
        connection_string=settings.azure_storage_connection_string,
        queue_name="ai-generation-tasks",  # Make sure this queue exists in Azure/Azurite
    )

    task_payload = {
        "task_type": "flashcards",
        "group_id": str(uuid4()),
        "project_id": str(uuid4()),
        "user_id": str(uuid4()),
    }

    console.print(f"[bold blue]Sending task payload:[/bold blue] {task_payload}")

    queue_svc.send_message(task_payload)

    console.print("[bold green]Task message sent to queue successfully![/bold green]")


if __name__ == "__main__":
    main()
