from typing import Dict, List
from .implementations.base import AgentType, AgentConfig

class AgentRegistry:
    _agents: Dict[AgentType, AgentConfig] = {}

    @classmethod
    def register(cls, config: AgentConfig) -> None:
        cls._agents[config.id] = config

    @classmethod
    def get(cls, agent_type: AgentType) -> AgentConfig:
        if agent_type not in cls._agents:
            raise ValueError(f"Agent {agent_type} is not registered")
        return cls._agents[agent_type]

    @classmethod
    def get_all(cls) -> List[AgentConfig]:
        return list(cls._agents.values())

