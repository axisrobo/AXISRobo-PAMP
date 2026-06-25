"""Tests for dashboard router."""
from __future__ import annotations

from datetime import datetime
from .conftest import make_client, reset_overrides, FakeResult


_PROJECT_ROW = {
    "id": 1, "project_id": "P001", "project_name": "Project Alpha",
    "project_manager": "user01", "project_manager_name": "Alice",
    "status": "Active", "start_date": None, "end_date": None,
    "is_favourite": True,
}
_REQUEST_ROW = {
    "id": 1, "request_id": "EA001", "request_name": "New API",
    "project_id": "P001", "status": "Draft",
    "create_at": datetime(2025, 1, 1), "update_at": datetime(2025, 1, 2),
    "priority": "High",
}
_ACTION_ROW = {
    "id": 1, "action_no": 1, "action_title": "Fix Bug",
    "project_id": "P001", "status": "Open",
    "due_date": None, "assignee": "user01", "assignee_name": "Alice",
    "priority": "Medium", "request_id": "EA001",
}
_STATS_ROW = {
    "total_projects": 5, "active_projects": 3,
    "total_requests": 10, "draft_requests": 2,
    "open_actions": 4, "overdue_actions": 1,
}
_QUEUE_ROW = {
    "id": 1, "request_id": "EA001", "request_name": "New API",
    "project_id": "P001", "project_name": "Alpha",
    "status": "Submitted", "priority": "High",
    "applicant": "user01", "applicant_name": "Alice",
    "create_at": datetime(2025, 1, 1),
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


class TestStats:
    def test_returns_stats(self):
        client = make_client(FakeResult([_STATS_ROW]))
        resp = client.get("/api/dashboard/stats")
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
        resp = client.get("/api/dashboard/stats")
        assert resp.status_code == 500
        reset_overrides()


class TestHomeStats:
    def test_returns_home_stats(self):
        client = make_client(
            FakeResult([_STATS_ROW]),
        )
        resp = client.get("/api/dashboard/home-stats")
        assert resp.status_code == 200
        reset_overrides()


class TestMyProjects:
    def test_returns_my_projects(self):
        client = make_client(FakeResult([_PROJECT_ROW]))
        resp = client.get("/api/dashboard/my-projects")
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
        resp = client.get("/api/dashboard/my-projects")
        assert resp.status_code == 500
        reset_overrides()


class TestMyRequests:
    def test_returns_my_requests(self):
        client = make_client(FakeResult([_REQUEST_ROW]))
        resp = client.get("/api/dashboard/my-requests")
        assert resp.status_code == 200
        reset_overrides()


class TestMyActions:
    def test_returns_my_actions(self):
        client = make_client(FakeResult([_ACTION_ROW]))
        resp = client.get("/api/dashboard/my-actions")
        assert resp.status_code == 200
        reset_overrides()


class TestRequestQueue:
    def test_returns_queue(self):
        client = make_client(
            FakeResult([_QUEUE_ROW]),
            FakeResult([], scalar_value=1),
        )
        resp = client.get("/api/dashboard/request-queue")
        assert resp.status_code == 200
        reset_overrides()

    def test_with_status_filter(self):
        client = make_client(
            FakeResult([_QUEUE_ROW]),
            FakeResult([], scalar_value=1),
        )
        resp = client.get("/api/dashboard/request-queue?status=Submitted")
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
        resp = client.get("/api/dashboard/request-queue")
        assert resp.status_code == 500
        reset_overrides()


class TestRequestQueueHeader:
    def test_returns_queue_header(self):
        client = make_client(FakeResult([{"total": 5, "submitted": 3, "in_review": 2}]))
        resp = client.get("/api/dashboard/request-queue-header")
        assert resp.status_code == 200
        reset_overrides()
