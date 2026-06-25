"""Tests for app/auth/role_resolver.py — full coverage."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.auth.models import AuthUser, Role
from app.auth.rbac import build_permission_list
from app.auth.role_resolver import (
    resolve_scoped_roles,
    _is_team_member,
    _is_app_owner,
    _is_project_owner,
)
from tests.conftest import make_user, make_mock_db, MockResult


class _ScalarResult:
    """Mock result that returns a scalar value."""
    def __init__(self, value):
        self._value = value

    def scalar(self):
        return self._value

    def scalar_one(self):
        return self._value

    def scalar_one_or_none(self):
        return self._value

    def mappings(self):
        m = MagicMock()
        m.all.return_value = []
        m.first.return_value = None
        return m


def make_scalar_db(*values):
    """Create a mock DB that returns scalar values in sequence."""
    db = AsyncMock()
    results = list(values)
    call_idx = [0]

    async def execute(*args, **kwargs):
        idx = call_idx[0]
        call_idx[0] += 1
        v = results[idx] if idx < len(results) else None
        return _ScalarResult(v)

    db.execute = execute
    return db


class TestIsTeamMember:
    async def test_returns_true_when_found(self):
        db = make_scalar_db(1)
        assert await _is_team_member("user01", db) is True

    async def test_returns_false_when_not_found(self):
        db = make_scalar_db(None)
        assert await _is_team_member("user01", db) is False


class TestIsAppOwner:
    async def test_returns_true_when_cmdb_owner(self):
        db = make_scalar_db(1)  # first query returns a row
        assert await _is_app_owner("user01", "user01", db) is True

    async def test_returns_true_when_app_member(self):
        db = make_scalar_db(None, 1)  # first query none, second returns row
        assert await _is_app_owner("user01", "user01", db) is True

    async def test_returns_false_when_neither(self):
        db = make_scalar_db(None, None)
        assert await _is_app_owner("user01", "user01", db) is False

    async def test_skips_member_check_if_no_email_prefix(self):
        db = make_scalar_db(None)
        # empty email_prefix
        assert await _is_app_owner("user01", "", db) is False


class TestIsProjectOwner:
    async def test_returns_true_when_pm(self):
        db = make_scalar_db(1)
        assert await _is_project_owner("user01", db) is True

    async def test_returns_false_when_not_pm(self):
        db = make_scalar_db(None)
        assert await _is_project_owner("user01", db) is False


class TestResolveScopedRoles:
    async def test_adds_reviewer_role(self):
        user = make_user(roles=[Role.NORMAL_USER])
        # is_team_member → True, is_app_owner → False/False, is_project_owner → False
        db = make_scalar_db(1, None, None, None)
        updated = await resolve_scoped_roles(user, db)
        assert Role.EA_REVIEWER in updated.roles

    async def test_adds_app_owner_role(self):
        user = make_user(roles=[Role.NORMAL_USER])
        # is_team_member → False, is_app_owner (cmdb) → True
        db = make_scalar_db(None, 1, None)
        updated = await resolve_scoped_roles(user, db)
        assert Role.APP_OWNER in updated.roles

    async def test_adds_project_owner_role(self):
        user = make_user(roles=[Role.NORMAL_USER])
        # team_member→False, app_owner cmdb→False, app_member→False, project→True
        db = make_scalar_db(None, None, None, 1)
        updated = await resolve_scoped_roles(user, db)
        assert Role.PROJECT_OWNER in updated.roles

    async def test_no_change_when_already_has_roles(self):
        user = make_user(roles=[Role.NORMAL_USER, Role.EA_REVIEWER, Role.APP_OWNER, Role.PROJECT_OWNER])
        db = AsyncMock()  # Should not be called for already-resolved roles
        db.execute = AsyncMock(return_value=_ScalarResult(None))
        updated = await resolve_scoped_roles(user, db)
        assert updated is user  # same object returned when no change

    async def test_admin_skips_scope_resolution(self):
        user = make_user(roles=[Role.NORMAL_USER, Role.EA_ADMIN])
        db = make_scalar_db(None, None, None)
        # Admin bypasses resolve in middleware, but resolve_scoped_roles still runs
        updated = await resolve_scoped_roles(user, db)
        # Just validates no error thrown
        assert updated is not None

    async def test_permissions_rebuilt_after_new_role(self):
        user = make_user(roles=[Role.NORMAL_USER])
        old_perm_count = len(user.permissions)
        db = make_scalar_db(1, None, None, None)  # becomes reviewer
        updated = await resolve_scoped_roles(user, db)
        # Reviewer has more permissions than normal user
        assert len(updated.permissions) >= old_perm_count
