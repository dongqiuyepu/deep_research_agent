from __future__ import annotations

from typing import Dict, List

from backend.agent.core.base import BaseMemory


class ShortTermMemory(BaseMemory):
    """In-memory session scope memory."""

    def __init__(self) -> None:
        self._store: Dict[str, dict] = {}

    async def update(self, user_id: str, info: dict) -> None:
        self._store[user_id] = info

    async def retrieve(self, user_id: str, keywords: List[str]) -> dict:
        return self._store.get(user_id, {})
