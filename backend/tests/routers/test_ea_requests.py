"""Tests for EA requests router."""
from __future__ import annotations

from datetime import datetime
from .conftest import (
    FakeResult,
    make_async_session_local_override,
    make_client,
    reset_overrides,
)


_REQUEST_ROW = {
    "id": 1, "request_id": "EA001", "request_name": "New API Gateway",
    "project_id": "P001", "project_name": "Project Alpha",
    "status": "Draft", "applicant": "user01", "applicant_name": "Alice",
    "request_type": "New Architecture", "priority": "High",
    "expected_completion_date": None, "meeting_ids": None,
    "create_by": "user01", "create_at": datetime(2025, 1, 1),
    "update_at": datetime(2025, 1, 2), "description": "Test request",
    "current_architecture": None, "proposed_architecture": None,
    "bcm_ids": None, "scope_change_summary": None, "owner": "user01",
    "owner_name": "Alice",
}

_DASHBOARD_ROW = {
    "total": 10, "draft": 2, "submitted": 3, "in_review": 1,
    "approved": 3, "rejected": 1, "withdrawn": 0,
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


class TestListRequests:
    def test_returns_paginated(self):
        client = make_client(
            FakeResult([_REQUEST_ROW]),
            FakeResult([], scalar_value=1),
        )
        resp = client.get("/api/ea-requests")
        assert resp.status_code == 200
        reset_overrides()

    def test_with_status_filter(self):
        client = make_client(
            FakeResult([_REQUEST_ROW]),
            FakeResult([], scalar_value=1),
        )
        resp = client.get("/api/ea-requests?status=Draft")
        assert resp.status_code == 200
        reset_overrides()

    def test_with_project_filter(self):
        client = make_client(
            FakeResult([_REQUEST_ROW]),
            FakeResult([], scalar_value=1),
        )
        resp = client.get("/api/ea-requests?projectId=P001")
        assert resp.status_code == 200
        reset_overrides()

    def test_empty_result(self):
        client = make_client(
            FakeResult([]),
            FakeResult([], scalar_value=0),
        )
        resp = client.get("/api/ea-requests")
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
        resp = client.get("/api/ea-requests")
        assert resp.status_code == 500
        reset_overrides()


class TestDashboard:
    def test_returns_stats(self):
        client = make_client(FakeResult([_DASHBOARD_ROW]))
        resp = client.get("/api/ea-requests/dashboard")
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
        resp = client.get("/api/ea-requests/dashboard")
        assert resp.status_code == 500
        reset_overrides()


class TestFilterOptions:
    def test_returns_filter_options(self):
        client = make_client(
            FakeResult([{"project_id": "P001", "project_name": "Alpha"}]),
            FakeResult([{"applicant": "user01", "applicant_name": "Alice"}]),
        )
        resp = client.get("/api/ea-requests/filter-options")
        assert resp.status_code == 200
        reset_overrides()


class TestGetRequest:
    def test_returns_request(self):
        client = make_client(FakeResult([_REQUEST_ROW]))
        resp = client.get("/api/ea-requests/1")
        assert resp.status_code == 200
        reset_overrides()

    def test_not_found_returns_404(self):
        client = make_client(FakeResult([]))
        resp = client.get("/api/ea-requests/9999")
        assert resp.status_code == 404
        reset_overrides()


class TestCreateRequest:
    def test_creates_request(self, monkeypatch):
        import app.architecture_review.ea_requests as ea_requests_router

        monkeypatch.setattr(
            ea_requests_router,
            "AsyncSessionLocal",
            make_async_session_local_override(FakeResult(fetchone_row=(53,))),
        )
        client = make_client(
            FakeResult(),
            FakeResult(),
            FakeResult([_REQUEST_ROW]),
        )
        resp = client.post("/api/ea-requests", json={
            "projectId": "P001",
            "requestName": "New API Request",
            "requestType": "New Architecture",
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
        resp = client.post("/api/ea-requests", json={"projectId": "P001", "requestName": "X"})
        assert resp.status_code == 500
        reset_overrides()


class TestUpdateRequest:
    def test_updates_request(self):
        client = make_client(
            FakeResult([_REQUEST_ROW]),  # get existing
            FakeResult([{"exists": 1}]),
            FakeResult(),
            FakeResult(),
            FakeResult([_REQUEST_ROW]),
        )
        resp = client.put("/api/ea-requests/1", json={"status": "Submitted"})
        assert resp.status_code == 200
        reset_overrides()

    def test_not_found_returns_404(self):
        client = make_client(FakeResult([]))
        resp = client.put("/api/ea-requests/9999", json={"status": "Submitted"})
        assert resp.status_code == 404
        reset_overrides()


class TestDeleteRequest:
    def test_not_found_returns_404(self):
        client = make_client(FakeResult([]))
        resp = client.delete("/api/ea-requests/9999")
        assert resp.status_code == 404
        reset_overrides()

    def test_deletes_request(self):
        from unittest.mock import AsyncMock, MagicMock
        from app.main import app
        from app.database import get_db
        from app.auth.dependencies import get_current_user
        from .conftest import override_current_user
        from fastapi.testclient import TestClient
        app.dependency_overrides[get_current_user] = override_current_user

        async def db_gen():
            db = AsyncMock()
            get_r = MagicMock()
            get_r.mappings.return_value.first.return_value = _REQUEST_ROW
            del_r = MagicMock()
            del_r.rowcount = 1
            call = [0]
            async def execute(*a, **kw):
                idx = call[0]; call[0] += 1
                return get_r if idx == 0 else del_r
            db.execute = execute
            db.commit = AsyncMock()
            yield db

        app.dependency_overrides[get_db] = db_gen
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.delete("/api/ea-requests/1")
        assert resp.status_code == 200
        reset_overrides()
