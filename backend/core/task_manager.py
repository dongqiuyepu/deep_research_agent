from __future__ import annotations

from typing import Dict

from backend.core.models import Task


class TaskManager:
    """In-memory task registry."""

    def __init__(self) -> None:
        self._tasks: Dict[str, Task] = {}

    def register(self, task: Task) -> None:
        self._tasks[task.id] = task

    def get(self, task_id: str) -> Task | None:
        return self._tasks.get(task_id)
