from __future__ import annotations

from typing import List

from backend.provider.search.base import BaseSearchProvider


class SerperProvider(BaseSearchProvider):
    async def search(self, query: str) -> List[dict]:
        raise NotImplementedError("SerperProvider.search")
