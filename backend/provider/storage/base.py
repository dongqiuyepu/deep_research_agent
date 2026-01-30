from __future__ import annotations

from abc import ABC, abstractmethod


class BaseStorageProvider(ABC):
    @abstractmethod
    async def save(self, key: str, value: dict) -> None:
        """Save a value by key."""

    @abstractmethod
    async def load(self, key: str) -> dict | None:
        """Load a value by key."""
