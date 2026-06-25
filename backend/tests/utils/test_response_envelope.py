"""Tests for app/utils/response_envelope.py — full coverage."""
from __future__ import annotations

import json
import pytest
from unittest.mock import AsyncMock, MagicMock

from starlette.testclient import TestClient
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response, PlainTextResponse
from starlette.routing import Route

from app.utils.response_envelope import (
    epoch_ms,
    is_bypass_path,
    is_json_content_type,
    is_envelope,
    default_message_for_status,
    build_envelope,
    envelope_response,
    _extract_message,
    ResponseEnvelopeMiddleware,
)


# ─── Pure function tests ─────────────────────────────────────────

class TestEpochMs:
    def test_returns_positive_integer(self):
        ts = epoch_ms()
        assert isinstance(ts, int)
        assert ts > 0


class TestIsBypassPath:
    def test_exact_bypass_path(self):
        assert is_bypass_path("/openapi.json") is True
        assert is_bypass_path("/docs") is True
        assert is_bypass_path("/redoc") is True

    def test_bypass_prefix_docs(self):
        assert is_bypass_path("/docs/oauth2-redirect") is True

    def test_bypass_prefix_export(self):
        assert is_bypass_path("/api/export/applications") is True

    def test_bypass_prefix_attachments(self):
        assert is_bypass_path("/api/ea-requests/attachments/file.pdf") is True

    def test_non_bypass_path(self):
        assert is_bypass_path("/api/applications") is False
        assert is_bypass_path("/api/health") is False


class TestIsJsonContentType:
    def test_none_returns_false(self):
        assert is_json_content_type(None) is False

    def test_empty_string_returns_false(self):
        assert is_json_content_type("") is False

    def test_application_json(self):
        assert is_json_content_type("application/json") is True

    def test_application_json_with_charset(self):
        assert is_json_content_type("application/json; charset=utf-8") is True

    def test_vnd_json(self):
        assert is_json_content_type("application/vnd.api+json") is True

    def test_text_html(self):
        assert is_json_content_type("text/html") is False

    def test_text_csv(self):
        assert is_json_content_type("text/csv") is False


class TestIsEnvelope:
    def test_valid_envelope(self):
        payload = {"code": 200, "message": "OK", "data": None, "timestamp": 123}
        assert is_envelope(payload) is True

    def test_missing_key(self):
        payload = {"code": 200, "message": "OK", "data": None}
        assert is_envelope(payload) is False

    def test_not_dict(self):
        assert is_envelope([1, 2, 3]) is False
        assert is_envelope("string") is False
        assert is_envelope(None) is False


class TestDefaultMessageForStatus:
    def test_known_codes(self):
        assert default_message_for_status(400) == "Invalid request parameters"
        assert default_message_for_status(401) == "Unauthorized or token expired"
        assert default_message_for_status(403) == "Forbidden"
        assert default_message_for_status(404) == "Resource not found"
        assert default_message_for_status(405) == "Method not allowed"
        assert default_message_for_status(500) == "Internal server error"

    def test_unknown_code(self):
        assert default_message_for_status(418) == "Request failed"


class TestBuildEnvelope:
    def test_basic_structure(self):
        env = build_envelope(code=200, message="OK", data={"key": "val"})
        assert env["code"] == 200
        assert env["message"] == "OK"
        assert env["data"] == {"key": "val"}
        assert "timestamp" in env

    def test_custom_timestamp(self):
        env = build_envelope(code=200, message="OK", data=None, timestamp=9999)
        assert env["timestamp"] == 9999


class TestEnvelopeResponse:
    def test_200_response(self):
        resp = envelope_response(status_code=200, message="OK", data={"id": 1})
        assert resp.status_code == 200
        body = json.loads(resp.body)
        assert body["code"] == 200
        assert body["data"] == {"id": 1}

    def test_404_response_uses_default_message(self):
        resp = envelope_response(status_code=404)
        body = json.loads(resp.body)
        assert body["code"] == 404
        assert "not found" in body["message"].lower()

    def test_custom_code_overrides_status(self):
        resp = envelope_response(status_code=200, code=201, message="Created", data=None)
        body = json.loads(resp.body)
        assert body["code"] == 201

    def test_headers_applied(self):
        resp = envelope_response(status_code=200, message="OK", data=None, headers={"X-Custom": "value"})
        assert resp.headers["X-Custom"] == "value"


class TestExtractMessage:
    def test_dict_with_message_key(self):
        assert _extract_message({"message": "Something went wrong"}, 500) == "Something went wrong"

    def test_dict_with_detail_key(self):
        assert _extract_message({"detail": "Not authorized"}, 401) == "Not authorized"

    def test_dict_with_error_key(self):
        assert _extract_message({"error": "Bad input"}, 400) == "Bad input"

    def test_empty_message_falls_back(self):
        assert _extract_message({"message": ""}, 404) == "Resource not found"

    def test_non_dict_falls_back(self):
        assert _extract_message("some string", 500) == "Internal server error"

    def test_none_falls_back(self):
        assert _extract_message(None, 400) == "Invalid request parameters"


# ─── Middleware integration tests (via Starlette test app) ────────

def _make_test_app(handler):
    """Build a minimal Starlette app with the middleware applied."""
    app = Starlette(routes=[Route("/test", handler)])
    app.add_middleware(ResponseEnvelopeMiddleware)
    return app


class TestResponseEnvelopeMiddleware:
    def test_wraps_plain_json(self):
        async def handler(request):
            return JSONResponse({"items": []})

        client = TestClient(_make_test_app(handler))
        resp = client.get("/test")
        body = resp.json()
        assert body["code"] == 200
        assert body["data"] == {"items": []}

    def test_bypass_export_path_not_wrapped(self):
        async def handler(request):
            return JSONResponse({"raw": True})

        app = Starlette(routes=[Route("/api/export/data", handler)])
        app.add_middleware(ResponseEnvelopeMiddleware)
        client = TestClient(app)
        resp = client.get("/api/export/data")
        # The response should NOT be double-wrapped
        body = resp.json()
        assert "raw" in body

    def test_non_json_response_not_wrapped(self):
        async def handler(request):
            return PlainTextResponse("hello world")

        client = TestClient(_make_test_app(handler))
        resp = client.get("/test")
        assert resp.text == "hello world"

    def test_already_wrapped_not_double_wrapped(self):
        existing = {"code": 200, "message": "OK", "data": "existing", "timestamp": 1}

        async def handler(request):
            return JSONResponse(existing)

        client = TestClient(_make_test_app(handler))
        resp = client.get("/test")
        body = resp.json()
        # Should not be double-wrapped
        assert body["data"] == "existing"
        assert "code" in body

    def test_error_response_with_message_field(self):
        async def handler(request):
            return JSONResponse({"message": "not found"}, status_code=404)

        client = TestClient(_make_test_app(handler))
        resp = client.get("/test")
        body = resp.json()
        assert body["code"] == 404
        assert "not found" in body["message"]

    def test_empty_body_handled(self):
        async def handler(request):
            return Response(content=b"", status_code=200, media_type="application/json")

        client = TestClient(_make_test_app(handler))
        resp = client.get("/test")
        # Should handle empty body gracefully
        body = resp.json()
        assert body["code"] == 200

    def test_invalid_json_body_returned_as_is(self):
        async def handler(request):
            return Response(content=b"not valid json", status_code=200, media_type="application/json")

        client = TestClient(_make_test_app(handler))
        resp = client.get("/test")
        assert resp.text == "not valid json"
