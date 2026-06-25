"""Tests for schedules router."""
from __future__ import annotations

from datetime import datetime
from .conftest import make_client, reset_overrides, FakeResult


_SCHEDULE_ROW = {
    "id": 1, "schedule_no": 1, "schedule_title": "Weekly Review",
    "project_id": "P001", "start_time": datetime(2025, 3, 1, 9, 0),
    "end_time": datetime(2025, 3, 1, 10, 0), "duration": 60,
    "recurrence_pattern": "weekly", "end_after": 10,
    "owner": "admin", "remark": None,
    "status": "Active", "for_project": None, "for_meeting": None,
}


def _bad_db():
    from unittest.mock import AsyncMock
    async def gen():
        db = AsyncMock()
        async def _raise(*a, **kw):
            raise RuntimeError("fail")
        db.execute = _raise
        db.rollback = AsyncMock()
        yield db
    return gen


class TestListSchedules:
    def test_returns_paginated(self):
        client = make_client(
            FakeResult([_SCHEDULE_ROW]),
            FakeResult([], scalar_value=1),
        )
        resp = client.get("/api/schedules")
        assert resp.status_code == 200
        reset_overrides()

    def test_status_filter(self):
        client = make_client(
            FakeResult([_SCHEDULE_ROW]),
            FakeResult([], scalar_value=1),
        )
        resp = client.get("/api/schedules?status=Active")
        assert resp.status_code == 200
        reset_overrides()

    def test_time_from_filter(self):
        client = make_client(
            FakeResult([_SCHEDULE_ROW]),
            FakeResult([], scalar_value=1),
        )
        resp = client.get("/api/schedules?timeFrom=2025-01-01T00:00:00")
        assert resp.status_code == 200
        reset_overrides()

    def test_db_error_returns_500(self):
        from app.main import app
        from app.database import get_db
        from app.auth.dependencies import get_current_user
        from .conftest import override_current_user
        from fastapi.testclient import TestClient
        app.dependency_overrides[get_current_user] = override_current_user
        app.dependency_overrides[get_db] = _bad_db()
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/api/schedules")
        assert resp.status_code == 500
        reset_overrides()


class TestCreateSchedule:
    def test_creates_schedule(self):
        client = make_client(FakeResult([_SCHEDULE_ROW]))
        resp = client.post("/api/schedules", json={
            "title": "Test", "startTime": "2025-03-01T09:00:00",
            "endTime": "2025-03-01T10:00:00",
        })
        assert resp.status_code in (200, 201)
        reset_overrides()

    def test_db_error_returns_500(self):
        from app.main import app
        from app.database import get_db
        from app.auth.dependencies import get_current_user
        from .conftest import override_current_user
        from fastapi.testclient import TestClient
        app.dependency_overrides[get_current_user] = override_current_user
        app.dependency_overrides[get_db] = _bad_db()
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post("/api/schedules", json={"title": "Test"})
        assert resp.status_code == 500
        reset_overrides()


class TestUpdateSchedule:
    def test_updates_schedule(self):
        client = make_client(FakeResult([_SCHEDULE_ROW]))
        resp = client.put("/api/schedules/1", json={"title": "Updated"})
        assert resp.status_code == 200
        reset_overrides()

    def test_not_found_returns_404(self):
        client = make_client(FakeResult([]))
        resp = client.put("/api/schedules/999", json={"title": "X"})
        assert resp.status_code == 404
        reset_overrides()


class TestDeleteSchedule:
    def test_deletes_schedule(self):
        from unittest.mock import AsyncMock, MagicMock
        from app.main import app
        from app.database import get_db
        from app.auth.dependencies import get_current_user
        from .conftest import override_current_user
        from fastapi.testclient import TestClient
        app.dependency_overrides[get_current_user] = override_current_user

        async def db_with_rowcount():
            db = AsyncMock()
            result = MagicMock()
            result.rowcount = 1
            db.execute = AsyncMock(return_value=result)
            db.commit = AsyncMock()
            yield db

        app.dependency_overrides[get_db] = db_with_rowcount
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.delete("/api/schedules/1")
        assert resp.status_code == 200
        reset_overrides()

    def test_not_found_returns_404(self):
        from unittest.mock import AsyncMock, MagicMock
        from app.main import app
        from app.database import get_db
        from app.auth.dependencies import get_current_user
        from .conftest import override_current_user
        from fastapi.testclient import TestClient
        app.dependency_overrides[get_current_user] = override_current_user

        async def db_zero():
            db = AsyncMock()
            result = MagicMock()
            result.rowcount = 0
            db.execute = AsyncMock(return_value=result)
            yield db

        app.dependency_overrides[get_db] = db_zero
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.delete("/api/schedules/999")
        assert resp.status_code == 404
        reset_overrides()
