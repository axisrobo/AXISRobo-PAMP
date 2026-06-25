"""Tests for app/auth/dependencies.py — full coverage of auth FastAPI dependencies."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException
from starlette.requests import Request

from app.auth.dependencies import get_current_user, require_auth, require_role, require_permission
from app.auth.models import Role
from tests.conftest import make_user


def _make_request(user=None):
    """Build a minimal mock Request with optional state.user."""
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/test",
        "query_string": b"",
        "headers": [],
    }
    req = Request(scope)
    req.state.user = user
    return req


class TestGetCurrentUser:
    async def test_returns_user_from_state(self):
        user = make_user()
        req = _make_request(user)
        result = await get_current_user(req)
        assert result is user

    async def test_raises_401_when_no_user(self):
        req = _make_request(None)
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(req)
        assert exc_info.value.status_code == 401


class TestRequireAuth:
    async def test_returns_user(self):
        user = make_user()
        result = await require_auth(user)
        assert result is user


class TestRequireRole:
    async def test_allows_matching_role(self):
        user = make_user(roles=[Role.NORMAL_USER, Role.EA_ADMIN])
        dep = require_role(Role.EA_ADMIN)
        result = await dep(user)
        assert result is user

    async def test_raises_403_for_wrong_role(self):
        user = make_user(roles=[Role.NORMAL_USER])
        dep = require_role(Role.EA_ADMIN)
        with pytest.raises(HTTPException) as exc_info:
            await dep(user)
        assert exc_info.value.status_code == 403

    async def test_allows_any_matching_role(self):
        user = make_user(roles=[Role.NORMAL_USER, Role.EA_REVIEWER])
        dep = require_role(Role.EA_ADMIN, Role.EA_REVIEWER)
        result = await dep(user)
        assert result is user


class TestRequirePermission:
    async def test_allows_permitted_resource(self):
        user = make_user(roles=[Role.NORMAL_USER, Role.EA_ADMIN])
        dep = require_permission("ea_request", "write")
        result = await dep(user)
        assert result is user

    async def test_raises_403_for_no_permission(self):
        user = make_user(roles=[Role.NORMAL_USER])
        # Normal user cannot delete ea_request
        dep = require_permission("application", "delete")
        with pytest.raises(HTTPException) as exc_info:
            await dep(user)
        assert exc_info.value.status_code == 403
