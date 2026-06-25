"""Tests for CMDB router."""
from __future__ import annotations

from .conftest import make_client, reset_overrides, FakeResult


_CMDB_ROW = {
    "app_id": "APP001", "name": "App One", "app_full_name": "Application One",
    "short_description": "Desc", "u_status": "Active",
    "app_ownership": "IT", "owned_by": "user01", "app_it_owner": "user01",
    "app_dt_owner": "user01", "app_operation_owner": "user01",
    "app_owner_tower": "EA", "app_owner_domain": "Finance",
    "app_operation_owner_tower": None, "app_operation_owner_domain": None,
    "portfolio_mgt": "EA", "app_classification": "Business",
    "app_solution_type": "SaaS", "u_service_area": None,
    "patch_level": None, "update_at": None, "decommissioned_at": None,
}


def _bad_db():
    from unittest.mock import AsyncMock
    async def gen():
        db = AsyncMock()
        async def _raise(*a, **kw):
            raise RuntimeError("fail")
        db.execute = _raise
        yield db
    return gen


class TestListCmdb:
    def test_returns_paginated(self):
        client = make_client(
            FakeResult([_CMDB_ROW]),
            FakeResult([], scalar_value=1),
        )
        resp = client.get("/api/cmdb")
        assert resp.status_code == 200
        reset_overrides()

    def test_app_id_filter(self):
        client = make_client(
            FakeResult([_CMDB_ROW]),
            FakeResult([], scalar_value=1),
        )
        resp = client.get("/api/cmdb?appId=APP001")
        assert resp.status_code == 200
        reset_overrides()

    def test_name_filter(self):
        client = make_client(
            FakeResult([_CMDB_ROW]),
            FakeResult([], scalar_value=1),
        )
        resp = client.get("/api/cmdb?name=App")
        assert resp.status_code == 200
        reset_overrides()

    def test_status_filter(self):
        client = make_client(
            FakeResult([_CMDB_ROW]),
            FakeResult([], scalar_value=1),
        )
        resp = client.get("/api/cmdb?status=Active")
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
        resp = client.get("/api/cmdb")
        assert resp.status_code == 500
        reset_overrides()


class TestGetCmdbDetail:
    def test_returns_detail(self):
        client = make_client(FakeResult([_CMDB_ROW]))
        resp = client.get("/api/cmdb/APP001")
        assert resp.status_code == 200
        reset_overrides()

    def test_not_found_returns_404(self):
        client = make_client(FakeResult([]))
        resp = client.get("/api/cmdb/NOTEXIST")
        assert resp.status_code == 404
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
        resp = client.get("/api/cmdb/APP001")
        assert resp.status_code == 500
        reset_overrides()
