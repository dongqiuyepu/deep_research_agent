from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


@dataclass
class Task:
    id: str
    keywords: List[str]
    context: Dict[str, Any]
    requirements: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_prompt(self) -> str:
        return (
            "You are an information gathering assistant.\n"
            f"keywords: {self.keywords}\n"
            f"context: {self.context}\n"
            f"requirements: {self.requirements}\n"
            "Respond in structured JSON."
        )


class EventType(str, Enum):
    THOUGHT = "thought"
    ACTION = "action"
    OBSERVATION = "observation"
    RESULT = "result"


@dataclass
class AgentEvent:
    type: EventType
    content: Any
    metadata: Dict[str, Any]
    timestamp: datetime

    @classmethod
    def thought(cls, task_id: str, content: str) -> "AgentEvent":
        return cls(EventType.THOUGHT, content, {"task_id": task_id}, datetime.utcnow())

    @classmethod
    def result(cls, task_id: str, content: Any, reason: str) -> "AgentEvent":
        return cls(
            EventType.RESULT,
            content,
            {"task_id": task_id, "reason": reason},
            datetime.utcnow(),
        )


@dataclass
class ExecutionPlan:
    steps: List[str]
    task_id: str


@dataclass
class ToolResult:
    output: Dict[str, Any]


@dataclass
class AgentResult:
    task_id: str
    data: Dict[str, Any]
    reason: str
