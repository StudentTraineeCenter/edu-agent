import base64
import json

from azure.storage.queue import QueueClient
from edu_shared.schemas.queue import QueueTaskMessage
from rich.console import Console

console = Console(force_terminal=True)


class QueueService:
    def __init__(self, connection_string: str, queue_name: str):
        self.queue_client = QueueClient.from_connection_string(
            conn_str=connection_string, queue_name=queue_name
        )

    def send_message(self, message: QueueTaskMessage) -> None:
        """
        Sends a QueueTaskMessage to the Azure Queue.
        Automatically handles Base64 encoding required by Azure Functions.
        """
        try:
            # 1. Convert dict to JSON string
            message_json = json.dumps(message)

            # 2. Base64 encode the string (Required for Azure Functions triggers)
            message_bytes = message_json.encode("utf-8")
            base64_message = base64.b64encode(message_bytes).decode("utf-8")

            # 3. Send to Azure
            self.queue_client.send_message(base64_message)
            console.print(
                f"[bold green]Message sent to queue: {self.queue_client.queue_name}[/bold green]"
            )

        except Exception as e:
            console.print(f"[bold red]Error sending message: {e!s}[/bold red]")
            raise e
