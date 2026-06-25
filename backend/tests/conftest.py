"""Shared test fixtures for the AxisArch authorization test suite.
 
Provides factory helpers for creating AuthUser instances with specific roles,
and a mock AsyncSession for testing ownership checks without a real database.
"""
from __future__ import annotations

import os
os.environ["EE_ENABLED"] = "true"  # Enable EE features for test suite

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.auth.models import AuthUser, Role
from app.auth.rbac import build_permission_list


# ---------------------------------------------------------------------------
# AuthUser factories
# ---------------------------------------------------------------------------

def make_user(
    *,
    user_id: str = "testuser",
    name: str = "Test User",
    email: str = "testuser@example.com",
    roles: list[Role] | None = None,
) -> AuthUser:
    """Create an AuthUser with the given roles and auto-computed permissions."""
    if roles is None:
        roles = [Role.NORMAL_USER]
    email_prefix = email.split("@")[0].lower()
    return AuthUser(
        id=user_id,
        name=name,
        email=email,
        email_prefix=email_prefix,
        roles=roles,
        permissions=build_permission_list(roles),
    )


@pytest.fixture
def admin_user() -> AuthUser:
    """EA_Admin user — unrestricted access."""
    return make_user(
        user_id="admin01",
        name="Admin User",
        email="admin01@example.com",
        roles=[Role.NORMAL_USER, Role.EA_ADMIN],
    )


@pytest.fixture
def normal_user() -> AuthUser:
    """Normal_User — baseline read-only access."""
    return make_user(
        user_id="user01",
        name="Normal User",
        email="user01@example.com",
        roles=[Role.NORMAL_USER],
    )


@pytest.fixture
def reviewer_user() -> AuthUser:
    """EA_Reviewer — can review assigned requests."""
    return make_user(
        user_id="reviewer01",
        name="Reviewer User",
        email="reviewer01@example.com",
        roles=[Role.NORMAL_USER, Role.EA_REVIEWER],
    )


@pytest.fixture
def app_owner_user() -> AuthUser:
    """App_Owner — can manage owned applications."""
    return make_user(
        user_id="appowner01",
        name="App Owner User",
        email="appowner01@example.com",
        roles=[Role.NORMAL_USER, Role.APP_OWNER],
    )


@pytest.fixture
def other_user() -> AuthUser:
    """Another Normal_User for testing cross-user scenarios."""
    return make_user(
        user_id="other99",
        name="Other User",
        email="other99@example.com",
        roles=[Role.NORMAL_USER],
    )


@pytest.fixture
def project_owner_user() -> AuthUser:
    """Project_Owner — can manage owned projects."""
    return make_user(
        user_id="projowner01",
        name="Project Owner User",
        email="projowner01@example.com",
        roles=[Role.NORMAL_USER, Role.PROJECT_OWNER],
    )


# ---------------------------------------------------------------------------
# Mock AsyncSession helpers
# ---------------------------------------------------------------------------

class MockResult:
    """Minimal mock for SQLAlchemy async result."""

    def __init__(self, rows: list[dict[str, Any]] | None = None, scalar_value: Any = None):
        self._rows = rows
        self._scalar_value = scalar_value

    def mappings(self) -> MockMappings:
        return MockMappings(self._rows or [])

    def scalar(self) -> Any:
        return self._scalar_value

    def fetchall(self) -> list[tuple]:
        if self._rows is None:
            return []
        # Return rows as tuples (first value of each dict)
        return [tuple(r.values()) for r in self._rows]


class MockMappings:
    """Mock for result.mappings()."""

    def __init__(self, rows: list[dict[str, Any]]):
        self._rows = rows

    def first(self) -> dict[str, Any] | None:
        return self._rows[0] if self._rows else None

    def all(self) -> list[dict[str, Any]]:
        return self._rows


def make_mock_db(execute_results: list[MockResult] | None = None) -> AsyncMock:
    """Create a mock AsyncSession that returns pre-configured results.

    ``execute_results`` is a list of MockResult objects. Each call to
    ``db.execute()`` pops the next result from the list.  If None or
    exhausted, returns an empty MockResult.
    """
    db = AsyncMock()
    results = list(execute_results or [])
    call_index = 0

    async def _execute(*args: Any, **kwargs: Any) -> MockResult:
        nonlocal call_index
        if call_index < len(results):
            result = results[call_index]
            call_index += 1
            return result
        return MockResult()

    db.execute = _execute
    return db
