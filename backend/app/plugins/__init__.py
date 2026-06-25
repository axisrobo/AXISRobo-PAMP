"""Enterprise integration plugins. Loaded at startup based on configuration."""
from __future__ import annotations
from typing import Any


class PluginRegistry:
    def __init__(self):
        self._providers: dict[str, Any] = {}

    def register(self, name: str, provider: Any) -> None:
        self._providers[name] = provider

    def get(self, name: str) -> Any | None:
        return self._providers.get(name)

    def get_or_default(self, name: str, default: Any) -> Any:
        return self._providers.get(name, default)


plugin_registry = PluginRegistry()
