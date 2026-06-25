"""Shared fixtures and helpers for router-level tests.

Pattern
-------
All router tests use FastAPI's dependency_overrides to replace:
  - ``get_current_user`` → returns a pre-built AuthUser (admin by default)
  - ``get_db``           → returns a mock AsyncSession

The ``TestClient`` from Starlette is used for synchronous HTTP calls; it
drives the async event loop internally.
"""
from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.auth.dependencies import get_current_user
from app.auth.models import Role
from app.database import get_db
from tests.conftest import make_user


_DEFAULT_FETCHONE = object()


# ─── Row helpers ─────────────────────────────────────────────────

class FakeRow(dict):
    """A dict sub-class that also exposes _mapping (like SQLAlchemy rows).

    Missing keys return ``None`` (tolerant) to avoid KeyError when router
    mapping code accesses fields not present in a minimal test row.
    """

    def __missing__(self, key: str):  # noqa: D105
        return None

    def get(self, key, default=None):  # noqa: D105
        val = super().get(key, None)
        if val is None:
            return default
        return val

    @property
    def _mapping(self):
        return self


class FakeResult:
    """Mock SQLAlchemy result object — covers all call patterns used in routers."""

    def __init__(
        self,
        rows: list[dict] | None = None,
        scalar_value: Any = 0,
        fetchone_row: Any = _DEFAULT_FETCHONE,
    ):
        self._rows = [FakeRow(r) for r in (rows or [])]
        self._scalar_value = scalar_value
        self._fetchone_row = fetchone_row

    # ── mapping access ──────────────────────────────────────────
    def mappings(self) -> "_FakeMappings":
        return _FakeMappings(self._rows)

    # ── scalar access ───────────────────────────────────────────
    def scalar(self) -> Any:
        return self._scalar_value

    def scalar_one(self) -> Any:
        return self._scalar_value

    def scalar_one_or_none(self) -> Any:
        return self._rows[0] if self._rows else None

    # ── fetchone / fetchall ────────────────────────────────────
    def fetchone(self) -> Any:
        if self._fetchone_row is not _DEFAULT_FETCHONE:
            return self._fetchone_row
        if self._rows:
            row = self._rows[0]
            return MagicMock(_mapping=row)
        return None

    def fetchall(self) -> list:
        return [MagicMock(_mapping=r) for r in self._rows]

    def first(self) -> Any:
        return self._rows[0] if self._rows else None


class _FakeMappings:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows

    def first(self):
        return self._rows[0] if self._rows else None


# ─── DB mock factory ─────────────────────────────────────────────

def make_db_override(*results: FakeResult):
    """Return an async generator factory that cycles through *results* on each execute().

    Pass multiple ``FakeResult`` objects for endpoints that call ``db.execute()``
    more than once (e.g. count + data queries).
    """
    result_list = list(results)

    async def _override():
        call_idx = [0]
        db = AsyncMock()

        async def execute(*args, **kwargs):
            idx = call_idx[0]
            call_idx[0] += 1
            if idx < len(result_list):
                return result_list[idx]
            return FakeResult()

        db.execute = execute
        db.commit = AsyncMock()
        db.rollback = AsyncMock()
        db.close = AsyncMock()
        yield db

    return _override


def make_async_session_local_override(*results: FakeResult):
    """Return a fake AsyncSessionLocal factory for code paths that open sessions directly."""

    result_list = list(results)
    call_idx = [0]
    db = AsyncMock()

    async def execute(*args, **kwargs):
        idx = call_idx[0]
        call_idx[0] += 1
        if idx < len(result_list):
            return result_list[idx]
        return FakeResult()

    db.execute = execute
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.close = AsyncMock()

    class _SessionContext:
        async def __aenter__(self):
            return db

        async def __aexit__(self, exc_type, exc, tb):
            return False

    def _factory():
        return _SessionContext()

    return _factory


# ─── Admin user override ──────────────────────────────────────────

ADMIN_USER = make_user(
    user_id="admin",
    email="admin@example.com",
    roles=[Role.NORMAL_USER, Role.EA_ADMIN],
)


def override_current_user():
    return ADMIN_USER


# ─── Client factory ───────────────────────────────────────────────

def make_client(*db_results: FakeResult, user=None) -> TestClient:
    """Build a TestClient with mocked DB and auth user.

    Import and use the real ``app`` instance from ``app.main``.
    """
    from app.main import app

    app.dependency_overrides[get_current_user] = override_current_user
    app.dependency_overrides[get_db] = make_db_override(*db_results)

    return TestClient(app, raise_server_exceptions=False)


def reset_overrides():
    from app.main import app
    app.dependency_overrides.clear()
