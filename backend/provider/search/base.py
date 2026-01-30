from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List


class BaseSearchProvider(ABC):
    @abstractmethod
    async def search(self, query: str) -> List[dict]:
        """Search query and return results."""
