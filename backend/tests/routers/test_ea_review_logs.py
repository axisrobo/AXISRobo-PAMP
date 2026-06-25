"""Tests for ea_review_logs router."""
from __future__ import annotations

from datetime import datetime
from .conftest import make_client, reset_overrides, FakeResult


_LOG_ROW = {
    "id": 1,
    "comment": "Approved",
    "create_at": datetime(2025, 1, 10, 9, 0),
    "operator": "admin",
    "operation": "approve",
    "project_id": "P001",
}


class TestGetEaReviewLogs:
    def setup_method(self):
        # Two DB calls: count + data
        self.client = make_client(
            FakeResult([_LOG_ROW], scalar_value=1),
            FakeResult([_LOG_ROW], scalar_value=1),
        )

    def teardown_method(self):
        reset_overrides()

    def test_returns_paginated(self):
        resp = self.client.get("/api/ea-review-logs")
        assert resp.status_code == 200
        body = resp.json()
        data = body.get("data") or body
        assert "data" in data or isinstance(data, list)

    def test_filter_by_project_id(self):
        resp = self.client.get("/api/ea-review-logs?projectId=P001")
        assert resp.status_code == 200

    def test_filter_by_operator(self):
        resp = self.client.get("/api/ea-review-logs?operator=admin")
        assert resp.status_code == 200

    def test_sort_by_valid_field(self):
        resp = self.client.get("/api/ea-review-logs?sortField=createdAt&sortOrder=asc")
        assert resp.status_code == 200

    def test_invalid_sort_falls_back_to_default(self):
        resp = self.client.get("/api/ea-review-logs?sortField=badfield&sortOrder=desc")
        assert resp.status_code == 200

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
                raise RuntimeError("DB error")
            db.execute = _raise
            yield db

        app.dependency_overrides[get_db] = bad_db
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/api/ea-review-logs")
        assert resp.status_code == 500
        reset_overrides()
