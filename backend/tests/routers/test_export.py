"""Tests for export router."""
from __future__ import annotations

from .conftest import make_client, reset_overrides, FakeResult


_EXPORT_ROW = {
    "id": 1, "name": "Record One", "status": "Active",
    "create_by": "admin", "create_at": "2025-01-01",
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


class TestExportEntity:
    def test_exports_certifications(self):
        client = make_client(FakeResult([_EXPORT_ROW]))
        resp = client.get("/api/export/certifications")
        assert resp.status_code == 200
        reset_overrides()

    def test_exports_projects(self):
        client = make_client(FakeResult([_EXPORT_ROW]))
        resp = client.get("/api/export/projects")
        assert resp.status_code == 200
        reset_overrides()

    def test_exports_ea_requests(self):
        client = make_client(FakeResult([_EXPORT_ROW]))
        resp = client.get("/api/export/ea-requests")
        assert resp.status_code == 200
        reset_overrides()

    def test_exports_meetings(self):
        client = make_client(FakeResult([_EXPORT_ROW]))
        resp = client.get("/api/export/meetings")
        assert resp.status_code == 200
        reset_overrides()

    def test_exports_actions(self):
        client = make_client(FakeResult([_EXPORT_ROW]))
        resp = client.get("/api/export/actions")
        assert resp.status_code == 200
        reset_overrides()

    def test_exports_technology_stack(self):
        client = make_client(FakeResult([_EXPORT_ROW]))
        resp = client.get("/api/export/technology-stack")
        assert resp.status_code == 200
        reset_overrides()

    def test_unknown_entity_returns_error(self):
        client = make_client()
        resp = client.get("/api/export/unknown-entity")
        assert resp.status_code in (400, 404, 422)
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
        resp = client.get("/api/export/actions")
        assert resp.status_code == 500
        reset_overrides()
