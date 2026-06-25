"""Tests for reports router — lead-time report."""
from __future__ import annotations

from datetime import datetime
from .conftest import make_client, reset_overrides, FakeResult


_REQUEST_ROW = {
    "id": 1,
    "request_id": "EA250001",
    "project_id": "P001",
    "status": "Completed",
    "create_at": datetime(2025, 1, 1),
}
_PROJECT_ROW = {"project_name": "Test Project"}
_LOG_ROW_SUBMIT = {"action": "Submit", "create_at": datetime(2025, 1, 2)}
_LOG_ROW_COMPLETE = {"action": "Completed", "create_at": datetime(2025, 1, 10)}


class TestLeadTimeReport:
    def test_returns_paginated(self):
        # Calls: data_query, count_query, proj_query, logs_query (per request row)
        client = make_client(
            FakeResult([_REQUEST_ROW]),              # requests
            FakeResult([], scalar_value=1),           # count
            FakeResult([_PROJECT_ROW]),               # project name
            FakeResult([_LOG_ROW_SUBMIT, _LOG_ROW_COMPLETE]),  # logs
        )
        resp = client.get("/api/reports/lead-time")
        assert resp.status_code == 200
        reset_overrides()

    def test_project_id_filter(self):
        client = make_client(
            FakeResult([_REQUEST_ROW]),
            FakeResult([], scalar_value=1),
            FakeResult([_PROJECT_ROW]),
            FakeResult([]),
        )
        resp = client.get("/api/reports/lead-time?projectId=P001")
        assert resp.status_code == 200
        reset_overrides()

    def test_status_filter(self):
        client = make_client(
            FakeResult([_REQUEST_ROW]),
            FakeResult([], scalar_value=1),
            FakeResult([_PROJECT_ROW]),
            FakeResult([]),
        )
        resp = client.get("/api/reports/lead-time?status=Completed")
        assert resp.status_code == 200
        reset_overrides()

    def test_no_requests_empty_results(self):
        client = make_client(
            FakeResult([]),
            FakeResult([], scalar_value=0),
        )
        resp = client.get("/api/reports/lead-time")
        assert resp.status_code == 200
        reset_overrides()

    def test_db_error_returns_500(self):
        from unittest.mock import AsyncMock
        from app.main import app
        from app.database import get_db
        from app.auth.dependencies import get_current_user
        from .conftest import override_current_user
        from fastapi.testclient import TestClient

        app.dependency_overrides[get_current_user] = override_current_user

        async def bad_db():
            db = AsyncMock()
            async def _raise(*a, **kw):
                raise RuntimeError("fail")
            db.execute = _raise
            yield db

        app.dependency_overrides[get_db] = bad_db
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/api/reports/lead-time")
        assert resp.status_code == 500
        reset_overrides()
