"""Tests for technology stack router."""
from __future__ import annotations

from datetime import date, datetime
from .conftest import make_client, reset_overrides, FakeResult


_STACK_ROW = {
    "id": 1, "record_id": "TS001", "product_name": "Python",
    "version": "3.11", "category": "Language",
    "vendor": "PSF", "lifecycle_status": "Active",
    "eol_date": None, "description": "Python language",
    "create_by": "admin", "create_at": datetime(2025, 1, 1),
    "update_at": datetime(2025, 1, 2), "tags": None,
}
_APP_ROW = {
    "app_id": "TS-APP001", "app_name": "My App",
    "record_id": "TS001", "create_by": "admin",
    "create_at": datetime(2025, 1, 1),
}
_CATALOG_ROW = {
    "id": 1, "item_id": "CAT001", "app_id": "TS-APP001",
    "record_id": "TS001", "version": "3.11",
    "usage_purpose": "Backend", "create_by": "admin",
    "create_at": datetime(2025, 1, 1),
}
_MEMBER_ROW = {
    "id": 1, "member_id": "MEM001", "app_id": "TS-APP001",
    "user_id": "user01", "user_name": "Alice", "role": "Owner",
    "create_by": "admin", "create_at": datetime(2025, 1, 1),
}
_LIFECYCLE_ROW = {
    "record_id": "TS001", "product_name": "Python",
    "version": "3.11", "lifecycle_status": "Active",
    "eol_date": None,
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


class TestListTechStack:
    def test_returns_paginated(self):
        client = make_client(
            FakeResult([_STACK_ROW]),
            FakeResult([], scalar_value=1),
        )
        resp = client.get("/api/tech-stack")
        assert resp.status_code == 200
        reset_overrides()

    def test_with_category_filter(self):
        client = make_client(
            FakeResult([_STACK_ROW]),
            FakeResult([], scalar_value=1),
        )
        resp = client.get("/api/tech-stack?category=Language")
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
        resp = client.get("/api/tech-stack")
        assert resp.status_code == 500
        reset_overrides()


class TestGetTechStack:
    def test_returns_record(self):
        client = make_client(FakeResult([_STACK_ROW]))
        resp = client.get("/api/tech-stack/TS001")
        assert resp.status_code == 200
        reset_overrides()

    def test_not_found_returns_404(self):
        client = make_client(FakeResult([]))
        resp = client.get("/api/tech-stack/NONEXISTENT")
        assert resp.status_code == 404
        reset_overrides()


class TestCreateTechStack:
    def test_creates_record(self):
        client = make_client(FakeResult([_STACK_ROW]))
        resp = client.post("/api/tech-stack", json={
            "productName": "Python", "version": "3.11", "category": "Language"
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
        resp = client.post("/api/tech-stack", json={"productName": "X"})
        assert resp.status_code == 500
        reset_overrides()


class TestUpdateTechStack:
    def test_updates_record(self):
        client = make_client(
            FakeResult([_STACK_ROW]),  # get existing
            FakeResult([_STACK_ROW]),  # update
        )
        resp = client.put("/api/tech-stack/TS001", json={"lifecycleStatus": "EOL"})
        assert resp.status_code == 200
        reset_overrides()

    def test_not_found_returns_404(self):
        client = make_client(FakeResult([]))
        resp = client.put("/api/tech-stack/NONEXISTENT", json={"lifecycleStatus": "EOL"})
        assert resp.status_code == 404
        reset_overrides()


class TestDeleteTechStack:
    def test_not_found_returns_404(self):
        client = make_client(FakeResult([]))
        resp = client.delete("/api/tech-stack/NONEXISTENT")
        assert resp.status_code == 404
        reset_overrides()

    def test_deletes_record(self):
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
            get_r.mappings.return_value.first.return_value = _STACK_ROW
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
        resp = client.delete("/api/tech-stack/TS001")
        assert resp.status_code == 200
        reset_overrides()


class TestCategories:
    def test_returns_categories(self):
        client = make_client(FakeResult([{"category": "Language"}]))
        resp = client.get("/api/tech-stack/categories")
        assert resp.status_code == 200
        reset_overrides()


class TestMasterOptions:
    def test_returns_options(self):
        client = make_client(FakeResult([_STACK_ROW]))
        resp = client.get("/api/tech-stack/master-options")
        assert resp.status_code == 200
        reset_overrides()


class TestLifecycle:
    def test_returns_lifecycle(self):
        client = make_client(
            FakeResult([_LIFECYCLE_ROW]),
            FakeResult([], scalar_value=1),
        )
        resp = client.get("/api/tech-stack/lifecycle")
        assert resp.status_code == 200
        reset_overrides()


class TestResourcePool:
    def test_returns_resource_pool(self):
        client = make_client(FakeResult([_STACK_ROW]))
        resp = client.get("/api/tech-stack/resource-pool")
        assert resp.status_code == 200
        reset_overrides()


class TestCmdbLookup:
    def test_returns_lookup(self):
        client = make_client(FakeResult([{"cmdb_id": "CMDB001", "name": "App"}]))
        resp = client.get("/api/tech-stack/cmdb-lookup")
        assert resp.status_code == 200
        reset_overrides()


class TestTechStackApps:
    def test_create_app(self):
        client = make_client(FakeResult([_APP_ROW]))
        resp = client.post("/api/tech-stack/apps", json={
            "appName": "My App", "recordId": "TS001"
        })
        assert resp.status_code in (200, 201)
        reset_overrides()

    def test_get_app(self):
        client = make_client(FakeResult([_APP_ROW]))
        resp = client.get("/api/tech-stack/apps/TS-APP001")
        assert resp.status_code == 200
        reset_overrides()

    def test_get_app_not_found(self):
        client = make_client(FakeResult([]))
        resp = client.get("/api/tech-stack/apps/NONEXISTENT")
        assert resp.status_code == 404
        reset_overrides()

    def test_delete_app(self):
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
            get_r.mappings.return_value.first.return_value = _APP_ROW
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
        resp = client.delete("/api/tech-stack/apps/TS-APP001")
        assert resp.status_code == 200
        reset_overrides()


class TestCatalogEndpoints:
    def test_list_catalog(self):
        client = make_client(FakeResult([_CATALOG_ROW]))
        resp = client.get("/api/tech-stack/apps/TS-APP001/catalog")
        assert resp.status_code == 200
        reset_overrides()

    def test_create_catalog_item(self):
        client = make_client(FakeResult([_CATALOG_ROW]))
        resp = client.post("/api/tech-stack/apps/TS-APP001/catalog", json={
            "recordId": "TS001", "version": "3.11"
        })
        assert resp.status_code in (200, 201)
        reset_overrides()

    def test_update_catalog_item(self):
        client = make_client(
            FakeResult([_CATALOG_ROW]),  # get
            FakeResult([_CATALOG_ROW]),  # update
        )
        resp = client.put("/api/tech-stack/apps/TS-APP001/catalog/CAT001", json={
            "usagePurpose": "Updated"
        })
        assert resp.status_code == 200
        reset_overrides()

    def test_delete_catalog_item(self):
        from unittest.mock import AsyncMock, MagicMock
        from app.main import app
        from app.database import get_db
        from app.auth.dependencies import get_current_user
        from .conftest import override_current_user
        from fastapi.testclient import TestClient
        app.dependency_overrides[get_current_user] = override_current_user

        async def db_gen():
            db = AsyncMock()
            del_r = MagicMock()
            del_r.rowcount = 1
            db.execute = AsyncMock(return_value=del_r)
            db.commit = AsyncMock()
            yield db

        app.dependency_overrides[get_db] = db_gen
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.delete("/api/tech-stack/apps/TS-APP001/catalog/CAT001")
        assert resp.status_code == 200
        reset_overrides()


class TestTeamMemberEndpoints:
    def test_list_team_members(self):
        client = make_client(FakeResult([_MEMBER_ROW]))
        resp = client.get("/api/tech-stack/apps/TS-APP001/team-members")
        assert resp.status_code == 200
        reset_overrides()

    def test_add_team_member(self):
        client = make_client(FakeResult([_MEMBER_ROW]))
        resp = client.post("/api/tech-stack/apps/TS-APP001/team-members", json={
            "userId": "user02", "role": "Developer"
        })
        assert resp.status_code in (200, 201)
        reset_overrides()

    def test_remove_team_member(self):
        from unittest.mock import AsyncMock, MagicMock
        from app.main import app
        from app.database import get_db
        from app.auth.dependencies import get_current_user
        from .conftest import override_current_user
        from fastapi.testclient import TestClient
        app.dependency_overrides[get_current_user] = override_current_user

        async def db_gen():
            db = AsyncMock()
            del_r = MagicMock()
            del_r.rowcount = 1
            db.execute = AsyncMock(return_value=del_r)
            db.commit = AsyncMock()
            yield db

        app.dependency_overrides[get_db] = db_gen
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.delete("/api/tech-stack/apps/TS-APP001/team-members/MEM001")
        assert resp.status_code == 204
        reset_overrides()


class TestOperateLog:
    def test_list_operate_log(self):
        client = make_client(FakeResult([{
            "id": 1, "app_id": "TS-APP001", "action": "create",
            "operator": "user01", "operate_time": datetime(2025, 1, 5),
        }]))
        resp = client.get("/api/tech-stack/apps/TS-APP001/operate-log")
        assert resp.status_code == 200
        reset_overrides()


class TestChecking:
    def test_create_checking(self):
        client = make_client(FakeResult([{"check_result": "Pass"}]))
        resp = client.post("/api/tech-stack/apps/TS-APP001/checking", json={})
        assert resp.status_code in (200, 201)
        reset_overrides()
