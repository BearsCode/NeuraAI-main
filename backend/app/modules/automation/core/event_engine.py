import asyncio
import json
from backend.app.modules.automation.core.queue import QueueManager
from backend.app.modules.automation.core.orchestrator import WorkflowEngine
from backend.app.modules.automation.agents.implementations.base import AgentType

class EventEngine:
    def __init__(self, queue_manager: QueueManager, workflow_engine: WorkflowEngine):
        self.queue_manager = queue_manager
        self.workflow_engine = workflow_engine
        self._running = False

    async def handle_webhook(self, payload: dict) -> dict:
        if payload.get("event") == "start_generation":
            initial_context = {
                "topic": payload.get("topic", "General topic"),
                "platform": payload.get("platform", "Instagram")
            }
            await self.queue_manager.enqueue("workflow_queue", json.dumps(initial_context))
            return {"status": "accepted"}

        return {"status": "ignored"}

    async def run_worker(self):
        self._running = True
        while self._running:
            item = await self.queue_manager.dequeue("workflow_queue")
            if item:
                try:
                    initial_context = json.loads(item)
                    await self.workflow_engine.execute_dag(initial_context, [AgentType.PUBLISHER])
                except Exception:
                    pass

            await asyncio.sleep(1)

    def stop_worker(self):
        self._running = False
