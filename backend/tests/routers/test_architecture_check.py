"""Tests for architecture check router."""
from __future__ import annotations

from datetime import datetime
from .conftest import make_client, reset_overrides, FakeResult


_CHECK_ROW = {
    "check_app_uuid": "uuid-app-001",
    "request_id": "EA001", "app_id": "APP001", "app_name": "App One",
    "check_result": "Pass", "check_status": "Draft",
    "reviewer": "user01", "reviewer_name": "Alice",
    "create_by": "admin", "create_at": datetime(2025, 1, 1),
    "update_at": datetime(2025, 1, 2),
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


class TestListArchitectureChecks:
    def test_returns_checks(self):
        client = make_client(FakeResult([_CHECK_ROW]))
        resp = client.get("/api/ea-requests/1/architecture-check")
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
        resp = client.get("/api/ea-requests/1/architecture-check")
        assert resp.status_code == 500
        reset_overrides()


class TestCreateArchitectureCheck:
    def test_creates_check(self):
        client = make_client(FakeResult([_CHECK_ROW]))
        resp = client.post("/api/ea-requests/1/architecture-check", json={
            "appId": "APP001",
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
        resp = client.post("/api/ea-requests/1/architecture-check", json={"appId": "X"})
        assert resp.status_code == 500
        reset_overrides()


class TestUpdateArchitectureCheck:
    def test_updates_check(self):
        client = make_client(
            FakeResult([_CHECK_ROW]),  # get
            FakeResult([_CHECK_ROW]),  # update
        )
        resp = client.put("/api/ea-requests/1/architecture-check/uuid-app-001", json={
            "checkResult": "Pass",
        })
        assert resp.status_code == 200
        reset_overrides()

    def test_not_found_returns_404(self):
        client = make_client(FakeResult([]))
        resp = client.put("/api/ea-requests/1/architecture-check/nonexistent", json={
            "checkResult": "Pass",
        })
        assert resp.status_code == 404
        reset_overrides()


class TestDeleteArchitectureCheck:
    def test_not_found_returns_404(self):
        client = make_client(FakeResult([]))
        resp = client.delete("/api/ea-requests/1/architecture-check/nonexistent")
        assert resp.status_code == 404
        reset_overrides()

    def test_deletes_check(self):
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
            get_r.mappings.return_value.first.return_value = _CHECK_ROW
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
        resp = client.delete("/api/ea-requests/1/architecture-check/uuid-app-001")
        assert resp.status_code == 200
        reset_overrides()


class TestConfirmArchitectureCheck:
    def test_confirms_check(self):
        client = make_client(
            FakeResult([_CHECK_ROW]),  # request ownership
            FakeResult([_CHECK_ROW]),  # confirm result
        )
        resp = client.post("/api/ea-requests/1/architecture-check/confirm", json={})
        assert resp.status_code in (200, 201)
        reset_overrides()
