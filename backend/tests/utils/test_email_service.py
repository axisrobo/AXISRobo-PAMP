"""Tests for app/utils/email_service.py — covers token parsing, caching, and send."""
from __future__ import annotations

import json
import time
import base64
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import app.utils.email_service as email_mod
from app.utils.email_service import _parse_token_expiry


class TestParseTokenExpiry:
    def _make_token(self, payload: dict) -> str:
        header = base64.urlsafe_b64encode(b'{"alg":"HS256"}').decode().rstrip("=")
        body_bytes = json.dumps(payload).encode()
        body = base64.urlsafe_b64encode(body_bytes).decode().rstrip("=")
        return f"{header}.{body}.signature"

    def test_valid_exp_claim_returned(self):
        token = self._make_token({"exp": 9999999999})
        assert _parse_token_expiry(token) == 9999999999.0

    def test_missing_exp_returns_zero(self):
        token = self._make_token({"sub": "user"})
        assert _parse_token_expiry(token) == 0.0

    def test_invalid_token_returns_zero(self):
        assert _parse_token_expiry("not.a.valid") == 0.0

    def test_wrong_parts_returns_zero(self):
        assert _parse_token_expiry("onlyone") == 0.0


class TestGetAccessToken:
    def _make_valid_token(self, exp_offset: int = 7200) -> str:
        exp = int(time.time()) + exp_offset
        payload = {"exp": exp}
        header = base64.urlsafe_b64encode(b'{"alg":"HS256"}').decode().rstrip("=")
        body = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
        return f"{header}.{body}.sig"

    async def test_cached_token_returned_when_valid(self):
        """If cached token is still valid, it should be returned without HTTP call."""
        token = self._make_valid_token(7200)
        email_mod._cached_token = token
        email_mod._token_expires_at = time.time() + 7200

        result = await email_mod._get_access_token()
        assert result == token

        # Reset
        email_mod._cached_token = None
        email_mod._token_expires_at = 0.0

    async def test_no_bct_sdk_key_raises(self, monkeypatch):
        email_mod._cached_token = None
        email_mod._token_expires_at = 0.0
        monkeypatch.setattr(email_mod.settings, "BCT_SDK_KEY", "")

        with pytest.raises(RuntimeError, match="BCT_SDK_KEY is not configured"):
            await email_mod._get_access_token()

    async def test_fetches_token_from_api(self, monkeypatch):
        email_mod._cached_token = None
        email_mod._token_expires_at = 0.0
        monkeypatch.setattr(email_mod.settings, "BCT_SDK_KEY", "test-key")
        monkeypatch.setattr(email_mod.settings, "BCT_TOKEN_URL", "https://bct.example.com")
        monkeypatch.setattr(email_mod.settings, "BCT_APP_CODE", "eam-app")

        token = self._make_valid_token(3600)
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": {"token": token}}
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("app.utils.email_service.httpx.AsyncClient", return_value=mock_client):
            result = await email_mod._get_access_token()

        assert result == token

        # Reset
        email_mod._cached_token = None
        email_mod._token_expires_at = 0.0

    async def test_raises_if_no_token_in_response(self, monkeypatch):
        email_mod._cached_token = None
        email_mod._token_expires_at = 0.0
        monkeypatch.setattr(email_mod.settings, "BCT_SDK_KEY", "test-key")
        monkeypatch.setattr(email_mod.settings, "BCT_TOKEN_URL", "https://bct.example.com")
        monkeypatch.setattr(email_mod.settings, "BCT_APP_CODE", "eam-app")

        mock_response = MagicMock()
        mock_response.json.return_value = {"data": {}}
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("app.utils.email_service.httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(RuntimeError, match="No access token"):
                await email_mod._get_access_token()

        email_mod._cached_token = None
        email_mod._token_expires_at = 0.0

    async def test_flat_access_token_key(self, monkeypatch):
        email_mod._cached_token = None
        email_mod._token_expires_at = 0.0
        monkeypatch.setattr(email_mod.settings, "BCT_SDK_KEY", "test-key")
        monkeypatch.setattr(email_mod.settings, "BCT_TOKEN_URL", "https://bct.example.com")
        monkeypatch.setattr(email_mod.settings, "BCT_APP_CODE", "eam-app")

        token = self._make_valid_token(3600)
        mock_response = MagicMock()
        mock_response.json.return_value = {"accessToken": token}
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("app.utils.email_service.httpx.AsyncClient", return_value=mock_client):
            result = await email_mod._get_access_token()

        assert result == token
        email_mod._cached_token = None
        email_mod._token_expires_at = 0.0
