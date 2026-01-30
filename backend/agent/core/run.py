from __future__ import annotations

from typing import AsyncIterator

from backend.agent.core.base import BaseAgent
from backend.core.models import AgentEvent, Task


async def agent_run_loop(agent: BaseAgent, task: Task) -> AsyncIterator[AgentEvent]:
    """ReAct-style execution loop skeleton."""
    async for event in agent.stream_run(task):
        yield event
