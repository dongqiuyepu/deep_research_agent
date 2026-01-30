from __future__ import annotations

from backend.agent.core.base import BaseAgent
from backend.core.models import AgentResult, Task
from backend.pipeline.content_cleaner import ContentCleaner
from backend.pipeline.data_validator import DataValidator
from backend.pipeline.web_parser import WebParser


class Orchestrator:
    """Hybrid execution orchestrator."""

    def __init__(self, agent: BaseAgent) -> None:
        self.agent = agent
        self.parser = WebParser()
        self.cleaner = ContentCleaner()
        self.validator = DataValidator()

    async def execute(self, mode: str, task: Task) -> AgentResult:
        if mode == "agent":
            return await self.agent.run(task)
        if mode == "pipeline":
            parsed = await self.parser.run("")
            cleaned = await self.cleaner.run(parsed)
            validated = await self.validator.run(cleaned)
            return AgentResult(task_id=task.id, data=validated, reason="pipeline")
        return await self.agent.run(task)
