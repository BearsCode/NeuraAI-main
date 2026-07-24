from backend.app.integrations.ai_client import AIClient
from backend.app.integrations.queue_client import QueueClient
from backend.app.integrations.storage_client import StorageClient

ai_client = AIClient()
storage_client = StorageClient()

__all__ = ["AIClient", "QueueClient", "StorageClient", "ai_client", "storage_client"]
