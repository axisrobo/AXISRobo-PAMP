"""Tests for app/auth/middleware.py — full coverage."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from starlette.testclient import TestClient
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.middleware.base import BaseHTTPMiddleware

from app.auth.middleware import AuthMiddleware, _is_public


class TestIsPublic:
    def test_health_path_is_public(self):
        assert _is_public("/api/health") is True

    def test_docs_path_is_public(self):
        assert _is_public("/docs") is True
        assert _is_public("/redoc") is True
        assert _is_public("/openapi.json") is True

    def test_docs_prefix_is_public(self):
        assert _is_public("/docs/oauth2-redirect") is True

    def test_api_path_is_not_public(self):
        assert _is_public("/api/applications") is False
        assert _is_public("/api/ea-requests") is False

    def test_health_check_path_is_public(self):
        assert _is_public("/api/health/check") is True


def _build_app_with_middleware():
    """Build a minimal Starlette test app with AuthMiddleware."""
    async def handler(request: Request):
        user = getattr(request.state, "user", None)
        return JSONResponse({"user_id": user.id if user else None})

    app = Starlette(routes=[
        Route("/api/protected", handler),
        Route("/api/health", handler),
        Route("/docs", handler),
    ])
    app.add_middleware(AuthMiddleware)
    return app


class TestAuthMiddleware:
    def test_public_path_skips_auth(self):
        """Public paths should not call the auth provider."""
        app = _build_app_with_middleware()

        mock_provider = AsyncMock()
        mock_provider.authenticate = AsyncMock(return_value=None)

        with patch("app.auth.middleware.get_auth_provider", return_value=mock_provider):
            client = TestClient(app, raise_server_exceptions=False)
            resp = client.get("/api/health")
        assert resp.status_code == 200
        # Auth provider should NOT be called for public paths
        mock_provider.authenticate.assert_not_called()

    def test_authenticated_user_injected(self):
        """If auth provider returns a user, it should be stored in request.state.user."""
        from tests.conftest import make_user
        from app.auth.models import Role
        user = make_user(roles=[Role.NORMAL_USER, Role.EA_ADMIN])  # admin to skip role resolution

        app = _build_app_with_middleware()

        mock_provider = AsyncMock()
        mock_provider.authenticate = AsyncMock(return_value=user)

        with patch("app.auth.middleware.get_auth_provider", return_value=mock_provider):
            with patch("app.auth.middleware.AsyncSessionLocal") as mock_session_cls:
                mock_session = AsyncMock()
                mock_session.__aenter__ = AsyncMock(return_value=mock_session)
                mock_session.__aexit__ = AsyncMock(return_value=None)
                mock_session_cls.return_value = mock_session
                client = TestClient(app, raise_server_exceptions=False)
                resp = client.get("/api/protected")

        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == user.id

    def test_invalid_token_returns_401(self):
        app = _build_app_with_middleware()

        mock_provider = AsyncMock()
        mock_provider.authenticate = AsyncMock(side_effect=ValueError("Token expired"))

        with patch("app.auth.middleware.get_auth_provider", return_value=mock_provider):
            client = TestClient(app, raise_server_exceptions=False)
            resp = client.get("/api/protected")

        assert resp.status_code == 401

    def test_unexpected_auth_error_returns_500(self):
        app = _build_app_with_middleware()

        mock_provider = AsyncMock()
        mock_provider.authenticate = AsyncMock(side_effect=RuntimeError("DB error"))

        with patch("app.auth.middleware.get_auth_provider", return_value=mock_provider):
            client = TestClient(app, raise_server_exceptions=False)
            resp = client.get("/api/protected")

        assert resp.status_code == 500

    def test_non_admin_user_gets_role_resolved(self):
        """Non-admin users should go through scoped role resolution."""
        from tests.conftest import make_user
        from app.auth.models import Role
        user = make_user(roles=[Role.NORMAL_USER])  # NOT admin

        app = _build_app_with_middleware()

        mock_provider = AsyncMock()
        mock_provider.authenticate = AsyncMock(return_value=user)

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        # execute returns None (no scoped roles)
        mock_result = MagicMock()
        mock_result.scalar.return_value = None
        mock_result.scalar_one.return_value = None
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        with patch("app.auth.middleware.get_auth_provider", return_value=mock_provider):
            with patch("app.auth.middleware.AsyncSessionLocal", return_value=mock_session):
                client = TestClient(app, raise_server_exceptions=False)
                resp = client.get("/api/protected")

        assert resp.status_code == 200

    def test_role_resolution_failure_does_not_block_request(self):
        """If role resolution fails, user still has baseline roles and request proceeds."""
        from tests.conftest import make_user
        from app.auth.models import Role
        user = make_user(roles=[Role.NORMAL_USER])

        app = _build_app_with_middleware()

        mock_provider = AsyncMock()
        mock_provider.authenticate = AsyncMock(return_value=user)

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.execute = AsyncMock(side_effect=RuntimeError("DB unreachable"))

        with patch("app.auth.middleware.get_auth_provider", return_value=mock_provider):
            with patch("app.auth.middleware.AsyncSessionLocal", return_value=mock_session):
                client = TestClient(app, raise_server_exceptions=False)
                resp = client.get("/api/protected")

        # Should still succeed — role resolution failure is non-fatal
        assert resp.status_code == 200
