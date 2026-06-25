"""Tests for BizCapability router."""
from __future__ import annotations

from datetime import datetime
from .conftest import make_client, reset_overrides, FakeResult


_BIZ_CAPABILITY_ROW = {
    "id": 1, "bc_id": "BC001", "bc_name": "Capability One",
    "bc_level": 3, "version": "2025",
    "process_id": "PROC001", "process_name": "Process One",
    "function_id": "FUNC001", "function_name": "Function One",
    "create_by": "admin", "create_at": datetime(2025, 1, 1),
    "update_at": datetime(2025, 1, 2),
}
_VERSION_ROW = {"version": "2025", "is_active": True}
_FILTER_ROW = {"bc_id": "BC001", "bc_name": "Capability One"}


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


class TestBizCapabilityVersions:
    def test_returns_versions(self):
        client = make_client(FakeResult([_VERSION_ROW]))
        resp = client.get("/api/biz-capability/versions")
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
        resp = client.get("/api/biz-capability/versions")
        assert resp.status_code == 500
        reset_overrides()


class TestBizCapabilityFilterOptions:
    def test_returns_filter_options(self):
        client = make_client(
            FakeResult([_FILTER_ROW]),
            FakeResult([{"process_id": "PROC001", "process_name": "Process One"}]),
        )
        resp = client.get("/api/biz-capability/filter-options")
        assert resp.status_code == 200
        reset_overrides()


class TestListBizCapability:
    def test_returns_paginated(self):
        client = make_client(
            FakeResult([_BIZ_CAPABILITY_ROW]),
            FakeResult([], scalar_value=1),
        )
        resp = client.get("/api/biz-capability")
        assert resp.status_code == 200
        reset_overrides()

    def test_with_version_filter(self):
        client = make_client(
            FakeResult([_BIZ_CAPABILITY_ROW]),
            FakeResult([], scalar_value=1),
        )
        resp = client.get("/api/biz-capability?version=2025")
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
        resp = client.get("/api/biz-capability")
        assert resp.status_code == 500
        reset_overrides()


class TestBizCapabilityImportValidate:
    def test_validates_file(self):
        client = make_client(FakeResult([]))
        csv_content = b"bcName,bcId\n"
        resp = client.post(
            "/api/biz-capability/import/validate",
            files={"file": ("biz-capability.csv", csv_content, "text/csv")},
        )
        assert resp.status_code in (200, 422)
        reset_overrides()


class TestBizCapabilityImport:
    def test_imports_file(self):
        client = make_client(FakeResult([]))
        csv_content = b"bcName,bcId\n"
        resp = client.post(
            "/api/biz-capability/import",
            files={"file": ("biz-capability.csv", csv_content, "text/csv")},
        )
        assert resp.status_code in (200, 422)
        reset_overrides()


class TestBizCapabilityExport:
    def test_exports_data(self):
        client = make_client(FakeResult([_BIZ_CAPABILITY_ROW]))
        resp = client.get("/api/biz-capability/export")
        assert resp.status_code == 200
        reset_overrides()
