"""Tests for audit-log router."""
from __future__ import annotations

from datetime import datetime
from .conftest import make_client, reset_overrides, FakeResult


_AUDIT_ROW = {
    "id": 1,
    "object_type": "project",
    "object_id": "P001",
    "field": "status",
    "old_value": "Draft",
    "new_value": "Active",
    "create_by": "admin",
    "create_time": datetime(2025, 1, 10),
    "project_id": "P001",
}

_PROCESS_LOG_ROW = {
    "id": 1,
    "request_id": "EA001",
    "stage": "Review",
    "action": "Approve",
    "remark": None,
    "operator": "admin",
    "create_time": datetime(2025, 1, 10),
}

_EMAIL_LOG_ROW = {
    "id": 1,
    "request_id": "EA001",
    "recipient": "user@example.com",
    "subject": "Test Email",
    "status": "sent",
    "error_message": None,
    "create_time": datetime(2025, 1, 10),
}


def _bad_db_gen():
    from unittest.mock import AsyncMock

    async def gen():
        db = AsyncMock()
        async def _raise(*a, **kw):
            raise RuntimeError("DB error")
        db.execute = _raise
        yield db

    return gen


class TestAuditLog:
    def test_returns_paginated(self):
        client = make_client(
            FakeResult([_AUDIT_ROW]),
            FakeResult([], scalar_value=1),
        )
        resp = client.get("/api/audit-log")
        assert resp.status_code == 200
        reset_overrides()

    def test_project_id_filter(self):
        client = make_client(
            FakeResult([_AUDIT_ROW]),
            FakeResult([], scalar_value=1),
        )
        resp = client.get("/api/audit-log?projectId=P001")
        assert resp.status_code == 200
        reset_overrides()

    def test_object_type_filter(self):
        client = make_client(
            FakeResult([_AUDIT_ROW]),
            FakeResult([], scalar_value=1),
        )
        resp = client.get("/api/audit-log?objectType=project")
        assert resp.status_code == 200
        reset_overrides()

    def test_field_filter(self):
        client = make_client(
            FakeResult([_AUDIT_ROW]),
            FakeResult([], scalar_value=1),
        )
        resp = client.get("/api/audit-log?field=status")
        assert resp.status_code == 200
        reset_overrides()

    def test_create_by_filter(self):
        client = make_client(
            FakeResult([_AUDIT_ROW]),
            FakeResult([], scalar_value=1),
        )
        resp = client.get("/api/audit-log?createBy=admin")
        assert resp.status_code == 200
        reset_overrides()

    def test_sort_asc(self):
        client = make_client(
            FakeResult([_AUDIT_ROW]),
            FakeResult([], scalar_value=1),
        )
        resp = client.get("/api/audit-log?sortField=createdAt&sortOrder=asc")
        assert resp.status_code == 200
        reset_overrides()

    def test_invalid_sort_falls_back(self):
        client = make_client(
            FakeResult([_AUDIT_ROW]),
            FakeResult([], scalar_value=1),
        )
        resp = client.get("/api/audit-log?sortField=invalid_col")
        assert resp.status_code == 200
        reset_overrides()

    def test_db_error_returns_500(self):
        from app.main import app
        from app.database import get_db
        from app.auth.dependencies import get_current_user
        from .conftest import override_current_user
        from fastapi.testclient import TestClient

        app.dependency_overrides[get_current_user] = override_current_user
        app.dependency_overrides[get_db] = _bad_db_gen()
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/api/audit-log")
        assert resp.status_code == 500
        reset_overrides()
