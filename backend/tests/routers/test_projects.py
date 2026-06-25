"""Tests for projects router."""
from __future__ import annotations

from datetime import date, datetime
from .conftest import make_client, reset_overrides, FakeResult


_PROJECT_ROW = {
    "id": 1, "project_id": "P001", "project_name": "Project Alpha",
    "project_manager": "user01", "project_manager_name": "Alice",
    "start_date": date(2025, 1, 1), "end_date": date(2025, 12, 31),
    "status": "Active", "description": "Test project", "domain": "EA",
    "create_by": "admin", "create_at": datetime(2025, 1, 1),
    "update_at": datetime(2025, 1, 2), "is_favourite": False,
    "team_members": None, "tags": None,
}
_TASK_ROW = {
    "id": 1, "task_name": "Design", "project_id": "P001",
    "start_date": date(2025, 1, 1), "end_date": date(2025, 3, 31),
    "status": "Not Started", "assignee": "user01",
}
_APP_ROW = {
    "app_id": "APP001", "app_name": "App One",
    "project_id": "P001", "added_at": datetime(2025, 1, 5),
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


class TestListProjects:
    def test_returns_paginated(self):
        client = make_client(
            FakeResult([_PROJECT_ROW]),
            FakeResult([], scalar_value=1),
        )
        resp = client.get("/api/projects")
        assert resp.status_code == 200
        reset_overrides()

    def test_with_status_filter(self):
        client = make_client(
            FakeResult([_PROJECT_ROW]),
            FakeResult([], scalar_value=1),
        )
        resp = client.get("/api/projects?status=Active")
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
        resp = client.get("/api/projects")
        assert resp.status_code == 500
        reset_overrides()


class TestGetProject:
    def test_returns_project(self):
        client = make_client(FakeResult([_PROJECT_ROW]))
        resp = client.get("/api/projects/P001")
        assert resp.status_code == 200
        reset_overrides()

    def test_not_found_returns_404(self):
        client = make_client(FakeResult([]))
        resp = client.get("/api/projects/NONEXISTENT")
        assert resp.status_code == 404
        reset_overrides()


class TestListProjectTasks:
    def test_returns_tasks(self):
        client = make_client(FakeResult([_TASK_ROW]))
        resp = client.get("/api/projects/P001/tasks")
        assert resp.status_code == 200
        reset_overrides()

    def test_empty_tasks(self):
        client = make_client(FakeResult([]))
        resp = client.get("/api/projects/P001/tasks")
        assert resp.status_code == 200
        reset_overrides()


class TestListProjectApplications:
    def test_returns_applications(self):
        client = make_client(FakeResult([_APP_ROW]))
        resp = client.get("/api/projects/P001/applications")
        assert resp.status_code == 200
        reset_overrides()


class TestCreateProject:
    def test_creates_project(self):
        client = make_client(FakeResult([_PROJECT_ROW]))
        resp = client.post("/api/projects", json={
            "projectId": "P002",
            "projectName": "New Project",
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
        resp = client.post("/api/projects", json={"projectId": "P002", "projectName": "X"})
        assert resp.status_code == 500
        reset_overrides()


class TestUpdateProject:
    def test_updates_project(self):
        client = make_client(
            FakeResult([_PROJECT_ROW]),  # get existing
            FakeResult([_PROJECT_ROW]),  # update result
        )
        resp = client.put("/api/projects/P001", json={"status": "Completed"})
        assert resp.status_code == 200
        reset_overrides()

    def test_not_found_returns_404(self):
        client = make_client(FakeResult([]))
        resp = client.put("/api/projects/NONEXISTENT", json={"status": "Completed"})
        assert resp.status_code == 404
        reset_overrides()


class TestDeleteProject:
    def test_not_found_returns_404(self):
        client = make_client(FakeResult([]))
        resp = client.delete("/api/projects/NONEXISTENT")
        assert resp.status_code == 404
        reset_overrides()

    def test_deletes_project(self):
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
            get_r.mappings.return_value.first.return_value = _PROJECT_ROW
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
        resp = client.delete("/api/projects/P001")
        assert resp.status_code == 200
        reset_overrides()


class TestProjectApplications:
    def test_add_application(self):
        client = make_client(
            FakeResult([_PROJECT_ROW]),  # project existence / ownership check
            FakeResult([]),  # duplicate link check
            FakeResult([]),  # CMDB lookup fallback to request body
            FakeResult([_APP_ROW]),
        )
        resp = client.post(
            "/api/projects/P001/applications",
            json={"appId": "APP001", "appName": "App One"},
        )
        assert resp.status_code in (200, 201)
        reset_overrides()

    def test_remove_application(self):
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
        resp = client.delete("/api/projects/P001/applications/APP001")
        assert resp.status_code in (200, 204)
        reset_overrides()


class TestChangeFavourite:
    def test_change_favourite(self):
        from unittest.mock import AsyncMock, MagicMock
        from app.main import app
        from app.database import get_db
        from app.auth.dependencies import get_current_user
        from .conftest import override_current_user
        from fastapi.testclient import TestClient
        app.dependency_overrides[get_current_user] = override_current_user

        async def db_gen():
            db = AsyncMock()
            upd_r = MagicMock()
            upd_r.rowcount = 1
            db.execute = AsyncMock(return_value=upd_r)
            db.commit = AsyncMock()
            yield db

        app.dependency_overrides[get_db] = db_gen
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post("/api/projects/change-favourite", json={
            "id": "P001", "favourite": True
        })
        assert resp.status_code in (200, 201)
        reset_overrides()
