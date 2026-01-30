from __future__ import annotations

from typing import Dict, Type

from backend.agent.core.base import BaseAgent, BaseMemory
from backend.agent.core.tool import BaseTool


class ComponentRegistry:
    """Simple registry for agents, tools, memories."""

    _agents: Dict[str, Type[BaseAgent]] = {}
    _tools: Dict[str, Type[BaseTool]] = {}
    _memories: Dict[str, Type[BaseMemory]] = {}

    @classmethod
    def register_agent(cls, name: str):
        def decorator(agent_class: Type[BaseAgent]):
            cls._agents[name] = agent_class
            return agent_class

        return decorator

    @classmethod
    def get_agent(cls, name: str) -> Type[BaseAgent]:
        if name not in cls._agents:
            raise ValueError(f"Agent '{name}' not registered")
        return cls._agents[name]

    @classmethod
    def register_tool(cls, name: str):
        def decorator(tool_class: Type[BaseTool]):
            cls._tools[name] = tool_class
            return tool_class

        return decorator

    @classmethod
    def get_tool(cls, name: str) -> Type[BaseTool]:
        if name not in cls._tools:
            raise ValueError(f"Tool '{name}' not registered")
        return cls._tools[name]

    @classmethod
    def register_memory(cls, name: str):
        def decorator(memory_class: Type[BaseMemory]):
            cls._memories[name] = memory_class
            return memory_class

        return decorator

    @classmethod
    def get_memory(cls, name: str) -> Type[BaseMemory]:
        if name not in cls._memories:
            raise ValueError(f"Memory '{name}' not registered")
        return cls._memories[name]
