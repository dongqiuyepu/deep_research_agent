from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncIterator


class BaseLLMProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, **kwargs: str) -> str:
        """Generate a response."""

    @abstractmethod
    async def stream_generate(self, prompt: str, **kwargs: str) -> AsyncIterator[str]:
        """Stream a response."""
