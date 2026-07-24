from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession


class BaseAgent(ABC):
    name: str = "base"
    description: str = ""

    @abstractmethod
    async def execute(
        self,
        session: AsyncSession,
        input_data: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        ...


class AgentRegistry:
    def __init__(self):
        self._agents: dict[str, BaseAgent] = {}

    def register(self, name: str, agent: BaseAgent) -> None:
        self._agents[name] = agent

    def get_agent(self, name: str) -> BaseAgent | None:
        return self._agents.get(name)

    def list_agents(self) -> list[dict]:
        return [
            {"name": name, "description": agent.description}
            for name, agent in self._agents.items()
        ]
