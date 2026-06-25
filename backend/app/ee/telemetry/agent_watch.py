"""Optional Agent Watch adapter for EA agent flows."""
from __future__ import annotations

import logging
import os
import uuid
from typing import Any

from app.config import settings

logger = logging.getLogger("eam.ea_agents.agent_watch")


class AgentWatchAdapter:
    def __init__(self) -> None:
        self._client = None
        self._enabled = False
        if not settings.AGENT_WATCH_ENABLED:
            return
        if not (
            settings.AGENT_WATCH_COLLECTOR_URL
            and settings.AGENT_WATCH_APIH_TOKEN_URL
            and settings.AGENT_WATCH_APIH_ACCOUNT
            and settings.AGENT_WATCH_APIH_KEY
            and settings.AGENT_WATCH_APIH_SECRET
        ):
            logger.warning("Agent Watch enabled but required configuration is incomplete")
            return
        try:
            from agent_watch_sdk import AgentWatchClient  # type: ignore

            if settings.AGENT_WATCH_TOKEN:
                os.environ["AGENT_WATCH_TOKEN"] = settings.AGENT_WATCH_TOKEN
            self._client = AgentWatchClient(
                collector_url=settings.AGENT_WATCH_COLLECTOR_URL,
                application_name=settings.AGENT_WATCH_APPLICATION_NAME,
                auth_type="mixed",
                api_key=settings.AGENT_WATCH_APIH_KEY,
                username=settings.AGENT_WATCH_APIH_ACCOUNT,
                password=settings.AGENT_WATCH_APIH_SECRET,
                token_url=settings.AGENT_WATCH_APIH_TOKEN_URL,
                verify_ssl=False,
            )
            self._enabled = True
        except ModuleNotFoundError:
            logger.warning("Agent Watch SDK is unavailable; continuing without telemetry")
        except Exception:
            logger.warning("Agent Watch initialization failed; continuing without telemetry", exc_info=True)

    @property
    def enabled(self) -> bool:
        return self._enabled and self._client is not None

    def generate_trace_id(self) -> str:
        if self.enabled and hasattr(self._client, "generate_trace_id"):
            return self._client.generate_trace_id()
        return uuid.uuid4().hex

    def generate_span_id(self) -> str:
        if self.enabled and hasattr(self._client, "generate_span_id"):
            return self._client.generate_span_id()
        return uuid.uuid4().hex

    def _call(self, method_name: str, payload: dict[str, Any]) -> None:
        if not self.enabled:
            return
        try:
            getattr(self._client, method_name)(**payload)
        except Exception:
            logger.warning("Agent Watch call failed: %s", method_name, exc_info=True)

    def send_request(self, **payload: Any) -> None:
        self._call("send_request", payload)

    def receive_request(self, **payload: Any) -> None:
        self._call("receive_request", payload)

    def receive_response(self, **payload: Any) -> None:
        self._call("send_response", payload)


agent_watch = AgentWatchAdapter()
