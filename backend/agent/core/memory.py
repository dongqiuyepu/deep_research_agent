from abc import ABC, abstractmethod
from typing import List

class BaseMemory(ABC):
    """Base class for memory implementations."""

    @abstractmethod
    async def update(self, user_id: str, info: dict) -> None:
        """Update memory store."""

    @abstractmethod
    async def retrieve(self, user_id: str, keywords: List[str]) -> dict:
        """Retrieve context by keywords."""
