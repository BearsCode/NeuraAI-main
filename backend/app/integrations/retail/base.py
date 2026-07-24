from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class RetailAdapter(ABC):
    @abstractmethod
    async def fetch_products(self, credentials: dict) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def check_connection(self, credentials: dict) -> bool:
        ...

    @staticmethod
    def _normalize_product(raw: dict[str, Any]) -> dict[str, Any]:
        ...


class RetailAdapterRegistry:
    _adapters: dict[str, type[RetailAdapter]] = {}

    @classmethod
    def register(cls, key: str, adapter: type[RetailAdapter]) -> None:
        cls._adapters[key] = adapter

    @classmethod
    def get(cls, key: str) -> type[RetailAdapter] | None:
        return cls._adapters.get(key)
