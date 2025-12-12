import base64
import json
import time

from azure.storage.queue import QueueClient, QueueMessage
from rich.console import Console

from config import get_settings

console = Console(force_terminal=True)


def process_message(msg: QueueMessage):
    with console.status("[bold green]Processing message...[/bold green]"):
        # Decode message
        content = json.loads(base64.b64decode(msg.content).decode("utf-8"))

        task_type = content.get("task_type")
        group_id = content.get("group_id")

        console.log(f"Received task: {task_type} for group: {group_id}")

        # Run AI Logic
        # service = FlashcardService(...)
        # service.generate_content(...)

        # Update DB status to COMPLETED
        # ...
        console.log(f"Completed task: {task_type} for group: {group_id}")


def main():
    settings = get_settings()

    queue = QueueClient.from_connection_string(
        settings.azure_storage_connection_string, "ai-generation-tasks"
    )

    console.print("[bold green]Worker started. Polling queue...[/bold green]")

    while True:
        # Get messages (visibility_timeout hides it from other workers for 5 mins)
        messages = queue.receive_messages(visibility_timeout=300, max_messages=5)
        for msg in messages:
            try:
                process_message(msg)
                # queue.delete_message(msg)  # Done!
            except Exception as e:
                print(f"Error: {e}")
                # Message reappears after timeout (retry mechanism)

        time.sleep(1)  # Prevent tight loop


if __name__ == "__main__":
    main()
