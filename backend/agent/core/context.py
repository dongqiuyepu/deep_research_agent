from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseContext(ABC):
    """Simple in-memory context store for a single task run."""

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        pass

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        pass

    @abstractmethod
    def clear(self) -> None:
        pass

class Context(BaseContext):
    def __init__(self) -> None:
        self._data: Dict[str, Any] = {}

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def clear(self) -> None:
        self._data.clear() 
