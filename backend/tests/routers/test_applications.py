"""Tests for applications router (app_solution)."""
from __future__ import annotations

from datetime import datetime
from .conftest import make_client, reset_overrides, FakeResult


_APP_ROW = {
    "app_id": "APP001", "app_name": "Application One",
    "app_short_name": "App1", "app_type": "Web",
    "status": "Production", "owner": "user01", "owner_name": "Alice",
    "domain": "Finance", "description": "Test app",
    "create_by": "admin", "create_at": datetime(2025, 1, 1),
    "update_at": datetime(2025, 1, 2),
}
_BCM_ROW = {
    "id": 1, "bcm_id": "BCM001",
    "app_id": "APP001", "app_name": "Application One",
    "bc_id": "BC001", "bc_name": "Business Capability One",
    "bc_level": 3, "version": "2025",
    "create_by": "admin", "create_at": datetime(2025, 1, 1),
}
_CMDB_ROW = {
    "objectId": "OBJ001", "objectName": "CMDBApp",
    "objectType": "Application", "status": "Active",
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


class TestCmdbList:
    def test_returns_cmdb_list(self):
        client = make_client(FakeResult([_CMDB_ROW]))
        resp = client.get("/api/applications/cmdb")
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
        resp = client.get("/api/applications/cmdb")
        assert resp.status_code == 500
        reset_overrides()


class TestListApplications:
    def test_returns_applications(self):
        client = make_client(
            FakeResult([_APP_ROW]),
            FakeResult([], scalar_value=1),
        )
        resp = client.get("/api/applications")
        assert resp.status_code == 200
        reset_overrides()

    def test_with_status_filter(self):
        client = make_client(
            FakeResult([_APP_ROW]),
            FakeResult([], scalar_value=1),
        )
        resp = client.get("/api/applications?status=Production")
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
        resp = client.get("/api/applications")
        assert resp.status_code == 500
        reset_overrides()


class TestBcmVersions:
    def test_returns_versions(self):
        client = make_client(FakeResult([{"version": "2025", "is_active": True}]))
        resp = client.get("/api/applications/bcm/versions")
        assert resp.status_code == 200
        reset_overrides()


class TestBcTree:
    def test_returns_bc_tree(self):
        client = make_client(FakeResult([{"bc_id": "BC001", "bc_name": "Capability 1", "bc_level": 1, "parent_id": None}]))
        resp = client.get("/api/applications/bcm/bc-tree")
        assert resp.status_code == 200
        reset_overrides()


class TestBcmFilterOptions:
    def test_returns_filter_options(self):
        client = make_client(
            FakeResult([{"version": "2025"}]),
            FakeResult([{"domain": "Finance"}]),
        )
        resp = client.get("/api/applications/bcm/filter-options")
        assert resp.status_code == 200
        reset_overrides()


class TestListBcm:
    def test_returns_bcm_list(self):
        client = make_client(
            FakeResult([_BCM_ROW]),
            FakeResult([], scalar_value=1),
        )
        resp = client.get("/api/applications/bcm")
        assert resp.status_code == 200
        reset_overrides()

    def test_with_version_filter(self):
        client = make_client(
            FakeResult([_BCM_ROW]),
            FakeResult([], scalar_value=1),
        )
        resp = client.get("/api/applications/bcm?version=2025")
        assert resp.status_code == 200
        reset_overrides()


class TestBcmExport:
    def test_returns_export(self):
        client = make_client(FakeResult([_BCM_ROW]))
        resp = client.get("/api/applications/bcm/export")
        assert resp.status_code == 200
        reset_overrides()


class TestCreateBcm:
    def test_creates_bcm(self):
        client = make_client(FakeResult([_BCM_ROW]))
        resp = client.post("/api/applications/bcm", json={
            "appId": "APP001", "bcId": "BC002", "version": "2025"
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
        resp = client.post("/api/applications/bcm", json={"appId": "APP001", "bcId": "BC002"})
        assert resp.status_code == 500
        reset_overrides()


class TestUpdateBcm:
    def test_updates_bcm(self):
        client = make_client(
            FakeResult([_BCM_ROW]),  # get existing
            FakeResult([_BCM_ROW]),  # update result
        )
        resp = client.put("/api/applications/bcm/1", json={"version": "2026"})
        assert resp.status_code == 200
        reset_overrides()

    def test_not_found_returns_404(self):
        client = make_client(FakeResult([]))
        resp = client.put("/api/applications/bcm/9999", json={"version": "2026"})
        assert resp.status_code == 404
        reset_overrides()


class TestDeleteBcm:
    def test_not_found_returns_404(self):
        client = make_client(FakeResult([]))
        resp = client.delete("/api/applications/bcm/9999")
        assert resp.status_code == 404
        reset_overrides()

    def test_deletes_bcm(self):
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
            get_r.mappings.return_value.first.return_value = _BCM_ROW
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
        resp = client.delete("/api/applications/bcm/1")
        assert resp.status_code == 200
        reset_overrides()
