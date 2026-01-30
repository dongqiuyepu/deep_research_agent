from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncIterator, List, Optional

from backend.agent.core.tool import BaseTool
from backend.core.models import AgentEvent, AgentResult, ExecutionPlan, Task
from backend.provider.llm.base import BaseLLMProvider


class BaseAgent(ABC):
    """Base class for all agents."""

    def __init__(
        self,
        name: str,
        llm_provider: BaseLLMProvider,
        tools: List[BaseTool],
        memory: Optional["BaseMemory"] = None,
        **kwargs,
    ) -> None:
        self.name = name
        self.llm = llm_provider
        self.tools = tools
        self.memory = memory
        self._config = kwargs

    @abstractmethod
    async def run(self, task: Task) -> AgentResult:
        """Execute task in batch mode."""

    @abstractmethod
    async def stream_run(self, task: Task) -> AsyncIterator[AgentEvent]:
        """Execute task in streaming mode."""

    @abstractmethod
    async def plan(self, task: Task) -> ExecutionPlan:
        """Create an execution plan."""


class BaseMemory(ABC):
    """Base class for memory implementations."""

    @abstractmethod
    async def update(self, user_id: str, info: dict) -> None:
        """Update memory store."""

    @abstractmethod
    async def retrieve(self, user_id: str, keywords: List[str]) -> dict:
        """Retrieve context by keywords."""
