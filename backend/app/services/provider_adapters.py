from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class ProviderRequest:
    provider_code: str
    correlation_id: str
    payload: dict[str, Any]


@dataclass(frozen=True)
class ProviderResult:
    ok: bool
    provider_code: str
    payload: dict[str, Any]
    error: str | None = None
    latency_ms: int = 0


class ProviderAdapter(ABC):
    provider_code: str

    @abstractmethod
    def search_showtimes(self, request: ProviderRequest) -> ProviderResult:
        raise NotImplementedError

    @abstractmethod
    def fetch_seat_layout(self, request: ProviderRequest) -> ProviderResult:
        raise NotImplementedError

    @abstractmethod
    def reserve(self, request: ProviderRequest) -> ProviderResult:
        raise NotImplementedError

    @abstractmethod
    def confirm(self, request: ProviderRequest) -> ProviderResult:
        raise NotImplementedError


class DemoBookMyShowAdapter(ProviderAdapter):
    provider_code = "BMS_DEMO"

    def search_showtimes(self, request: ProviderRequest) -> ProviderResult:
        return ProviderResult(
            ok=True,
            provider_code=self.provider_code,
            payload={
                "source": "demo",
                "query": request.payload,
                "fetched_at": datetime.utcnow().isoformat(),
                "retryable": False,
            },
            latency_ms=38,
        )

    def fetch_seat_layout(self, request: ProviderRequest) -> ProviderResult:
        return ProviderResult(ok=True, provider_code=self.provider_code, payload={"layout_source": "local-cache"}, latency_ms=21)

    def reserve(self, request: ProviderRequest) -> ProviderResult:
        return ProviderResult(ok=True, provider_code=self.provider_code, payload={"reservation_state": "HELD"}, latency_ms=44)

    def confirm(self, request: ProviderRequest) -> ProviderResult:
        return ProviderResult(ok=True, provider_code=self.provider_code, payload={"confirmation_state": "CONFIRMED"}, latency_ms=57)


class ProviderRegistry:
    def __init__(self) -> None:
        self._adapters: dict[str, ProviderAdapter] = {}

    def register(self, adapter: ProviderAdapter) -> None:
        self._adapters[adapter.provider_code] = adapter

    def get(self, provider_code: str) -> ProviderAdapter:
        if provider_code not in self._adapters:
            raise KeyError(f"Provider adapter not registered: {provider_code}")
        return self._adapters[provider_code]

    def list_codes(self) -> list[str]:
        return sorted(self._adapters)


provider_registry = ProviderRegistry()
provider_registry.register(DemoBookMyShowAdapter())
