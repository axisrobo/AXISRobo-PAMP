"""HTTP client/response wrappers that auto-unwrap the API envelope.

Most existing API tests were written against the pre-envelope responses where
`resp.json()` returned the business payload directly.

After introducing a unified response envelope on the backend, these wrappers
preserve the old ergonomics by returning `envelope.data` for successful
responses (code == 200) while still allowing access to the original envelope
via `resp.envelope_json()`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

import httpx


def is_envelope(obj: Any) -> bool:
    return (
        isinstance(obj, dict)
        and "code" in obj
        and "message" in obj
        and "data" in obj
        and "timestamp" in obj
    )


@dataclass
class EnvelopedResponse:
    """Thin wrapper over httpx.Response with envelope-aware .json()."""

    _resp: httpx.Response

    def __getattr__(self, name: str):
        return getattr(self._resp, name)

    def envelope_json(self) -> Any:
        """Return the raw JSON body (envelope or legacy)."""
        return self._resp.json()

    def json(self, **kwargs) -> Any:
        """Return business payload for successful enveloped responses.

        - If response JSON is an envelope and code == 200 -> return envelope.data
        - Otherwise -> return raw JSON (legacy shape or error envelope)
        """
        body = self._resp.json(**kwargs)
        if is_envelope(body) and body.get("code") == 200:
            return body.get("data")
        return body


@runtime_checkable
class _RequestClient(Protocol):
    def request(self, method: str, url: str, **kwargs) -> httpx.Response: ...


class EnvelopedClient:
    """Client wrapper that returns EnvelopedResponse objects."""

    def __init__(self, client: _RequestClient):
        self._client = client

    def __getattr__(self, name: str):
        return getattr(self._client, name)

    def request(self, method: str, url: str, **kwargs) -> EnvelopedResponse:
        return EnvelopedResponse(self._client.request(method, url, **kwargs))

    def get(self, url: str, **kwargs) -> EnvelopedResponse:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs) -> EnvelopedResponse:
        return self.request("POST", url, **kwargs)

    def put(self, url: str, **kwargs) -> EnvelopedResponse:
        return self.request("PUT", url, **kwargs)

    def delete(self, url: str, **kwargs) -> EnvelopedResponse:
        return self.request("DELETE", url, **kwargs)
