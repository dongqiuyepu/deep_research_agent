from __future__ import annotations

from backend.provider.storage.base import BaseStorageProvider


class LocalStorage(BaseStorageProvider):
    def __init__(self) -> None:
        self._store: dict = {}

    async def save(self, key: str, value: dict) -> None:
        self._store[key] = value

    async def load(self, key: str) -> dict | None:
        return self._store.get(key)
