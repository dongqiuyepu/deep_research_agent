from __future__ import annotations

from typing import AsyncIterator

from backend.provider.llm.base import BaseLLMProvider


class OpenAIProvider(BaseLLMProvider):
    async def generate(self, prompt: str, **kwargs: str) -> str:
        raise NotImplementedError("OpenAIProvider.generate")

    async def stream_generate(self, prompt: str, **kwargs: str) -> AsyncIterator[str]:
        raise NotImplementedError("OpenAIProvider.stream_generate")
