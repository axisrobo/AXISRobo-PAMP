"""Unified API response envelope utilities.

This module defines the canonical JSON response envelope used by the backend.

Envelope shape:
  {
    "code": 200,
    "message": "OK",
    "data": <any JSON or null>,
    "timestamp": 1621234567890
  }

Bypass rules (responses NOT wrapped):
- OpenAPI and docs: /openapi.json, /docs, /redoc
- CSV export: /api/export/* (StreamingResponse)
- File download endpoints (best-effort path prefixes) and any non-JSON Content-Type

Implementation note:
- The response wrapper middleware uses both path-based bypass and Content-Type
  detection. If Content-Type is not JSON, the response is returned as-is.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Mapping, MutableMapping

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


JSON_CONTENT_TYPES = ("application/json", "+json")

# Paths that MUST NOT be wrapped.
BYPASS_PATHS: set[str] = {
    "/openapi.json",
    "/docs",
    "/redoc",
}

# Path prefixes that MUST NOT be wrapped.
BYPASS_PREFIXES: tuple[str, ...] = (
    "/docs",
    "/redoc",
    "/api/export",
    # Best-effort: some deployments expose attachment downloads under this prefix.
    "/api/ea-requests/attachments",
)


def epoch_ms() -> int:
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def is_bypass_path(path: str) -> bool:
    if path in BYPASS_PATHS:
        return True
    return any(path.startswith(prefix) for prefix in BYPASS_PREFIXES)


def is_json_content_type(content_type: str | None) -> bool:
    if not content_type:
        return False
    ct = content_type.lower()
    return any(token in ct for token in JSON_CONTENT_TYPES)


def is_envelope(payload: Any) -> bool:
    if not isinstance(payload, dict):
        return False
    return {
        "code",
        "message",
        "timestamp",
        "data",
    }.issubset(payload.keys())


def default_message_for_status(status_code: int) -> str:
    return {
        400: "Invalid request parameters",
        401: "Unauthorized or token expired",
        403: "Forbidden",
        404: "Resource not found",
        405: "Method not allowed",
        500: "Internal server error",
    }.get(status_code, "Request failed")


def build_envelope(*, code: int, message: str, data: Any, timestamp: int | None = None) -> dict[str, Any]:
    return {
        "code": code,
        "message": message,
        "data": data,
        "timestamp": epoch_ms() if timestamp is None else timestamp,
    }


def envelope_response(
    *,
    status_code: int,
    message: str | None = None,
    data: Any = None,
    code: int | None = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    """Build a JSONResponse using the envelope contract."""
    body = build_envelope(
        code=status_code if code is None else code,
        message=default_message_for_status(status_code) if not message else message,
        data=data,
    )
    resp = JSONResponse(status_code=status_code, content=body)
    if headers:
        for k, v in headers.items():
            resp.headers[k] = v
    return resp


def _extract_message(payload: Any, status_code: int) -> str:
    if isinstance(payload, dict):
        for key in ("message", "detail", "error"):
            val = payload.get(key)
            if isinstance(val, str) and val.strip():
                return val
    return default_message_for_status(status_code)


class ResponseEnvelopeMiddleware(BaseHTTPMiddleware):
    """Wrap JSON responses in the unified envelope.

    Notes:
    - Always skips bypass paths.
    - Always skips non-JSON Content-Type.
    - Avoids double-wrapping if the payload is already an envelope.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        if is_bypass_path(request.url.path):
            return response

        if not is_json_content_type(response.headers.get("content-type")):
            return response

        # Consume body (response.body may be empty when using streaming responses).
        body_bytes = b""
        async for chunk in response.body_iterator:
            body_bytes += chunk

        payload: Any
        if not body_bytes:
            payload = None
        else:
            try:
                payload = json.loads(body_bytes)
            except Exception:
                # If it isn't valid JSON, return as-is (but we must recreate the response
                # because we've consumed the iterator).
                return Response(
                    content=body_bytes,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type,
                )

        if is_envelope(payload):
            wrapped = payload
        else:
            if response.status_code >= 400:
                wrapped = build_envelope(
                    code=response.status_code,
                    message=_extract_message(payload, response.status_code),
                    data=None,
                )
            else:
                wrapped = build_envelope(code=200, message="OK", data=payload)

        new_response = JSONResponse(status_code=response.status_code, content=wrapped)

        # Preserve headers (especially CORS), but let JSONResponse manage Content-*.
        for k, v in response.headers.items():
            lk = k.lower()
            if lk in {"content-length", "content-type"}:
                continue
            new_response.headers[k] = v

        return new_response
