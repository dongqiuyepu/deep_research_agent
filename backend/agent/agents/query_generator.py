from __future__ import annotations

from typing import AsyncIterator, List

from backend.agent.core.base import BaseAgent
from backend.core.models import AgentEvent, AgentResult, ExecutionPlan, Task
from backend.core.schemas import QueryGenerationOutput
from backend.utils.parsers import parse_llm_response


class QueryGeneratorAgent(BaseAgent):
    """Agent that generates search queries."""

    async def run(self, task: Task) -> AgentResult:
        prompt = task.to_prompt()
        raw = await self.llm.generate(prompt)
        parsed = parse_llm_response(raw, QueryGenerationOutput)
        return AgentResult(
            task_id=task.id,
            data={
                "queries": parsed.queries,
                "search_strategy": parsed.search_strategy,
                "metadata": parsed.metadata,
            },
            reason=parsed.reason,
        )

    async def stream_run(self, task: Task) -> AsyncIterator[AgentEvent]:
        yield AgentEvent.thought(task.id, "generate search queries")
        result = await self.run(task)
        yield AgentEvent.result(task.id, result.data, reason=result.reason)

    async def plan(self, task: Task) -> ExecutionPlan:
        return ExecutionPlan(steps=["generate_queries"], task_id=task.id)


class InfoGathererAgent(BaseAgent):
    """Agent that gathers information via tools."""

    async def run(self, task: Task) -> AgentResult:
        raise NotImplementedError("InfoGathererAgent.run")

    async def stream_run(self, task: Task) -> AsyncIterator[AgentEvent]:
        raise NotImplementedError("InfoGathererAgent.stream_run")

    async def plan(self, task: Task) -> ExecutionPlan:
        return ExecutionPlan(steps=["search", "fetch", "parse"], task_id=task.id)


class ReportWriterAgent(BaseAgent):
    """Agent that writes structured reports."""

    async def run(self, task: Task) -> AgentResult:
        raise NotImplementedError("ReportWriterAgent.run")

    async def stream_run(self, task: Task) -> AsyncIterator[AgentEvent]:
        raise NotImplementedError("ReportWriterAgent.stream_run")

    async def plan(self, task: Task) -> ExecutionPlan:
        return ExecutionPlan(steps=["summarize", "format"], task_id=task.id)
