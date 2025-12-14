"""Queue service for sending messages to Azure Queue."""

import base64
import json
import logging

from azure.storage.queue import QueueClient

from edu_shared.schemas.queue import QueueTaskMessage

logger = logging.getLogger(__name__)


class QueueService:
    """Service for sending messages to Azure Queue."""

    def __init__(self, connection_string: str, queue_name: str):
        """Initialize the queue service.

        Args:
            connection_string: Azure Storage connection string
            queue_name: Name of the queue
        """
        self.queue_client = QueueClient.from_connection_string(
            conn_str=connection_string, queue_name=queue_name
        )

    def send_message(self, message: QueueTaskMessage) -> None:
        """
        Sends a QueueTaskMessage to the Azure Queue.
        Automatically handles Base64 encoding required by Azure Functions.

        Args:
            message: The queue task message to send

        Raises:
            Exception: If sending the message fails
        """
        try:
            # 1. Convert dict to JSON string
            message_json = json.dumps(message)

            # 2. Base64 encode the string (Required for Azure Functions triggers)
            message_bytes = message_json.encode("utf-8")
            base64_message = base64.b64encode(message_bytes).decode("utf-8")

            # 3. Send to Azure
            self.queue_client.send_message(base64_message)
            logger.info(f"Message sent to queue: {self.queue_client.queue_name}")

        except Exception as e:
            logger.error(f"Error sending message: {e!s}")
            raise e
