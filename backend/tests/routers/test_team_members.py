"""Tests for team-members router."""
from __future__ import annotations

from .conftest import make_client, reset_overrides, FakeResult, make_db_override


_MEMBER_ROW = {
    "itcode": "user01",
    "name": "Alice",
    "email": "alice@example.com",
    "worker": "FTE",
    "worker_type": "FTE",
    "country": "CN",
    "location": "Beijing",
    "primary_skill": "Java",
    "skill_level": "Senior",
    "job_role": "Developer",
    "track_focal": None,
    "manager_itcode": None,
    "manager_name": None,
    "email_option": None,
    "ea_admin_status": None,
    "tier_1_org": "IT",
    "tier_2_org": "EA",
}


def _bad_db():
    from unittest.mock import AsyncMock
    async def gen():
        db = AsyncMock()
        async def _raise(*a, **kw):
            raise RuntimeError("DB error")
        db.execute = _raise
        db.rollback = AsyncMock()
        yield db
    return gen


class TestListTeamMembers:
    def test_returns_paginated(self):
        client = make_client(
            FakeResult([_MEMBER_ROW]),
            FakeResult([], scalar_value=1),
        )
        resp = client.get("/api/team-members")
        assert resp.status_code == 200
        reset_overrides()

    def test_itcode_filter(self):
        client = make_client(
            FakeResult([_MEMBER_ROW]),
            FakeResult([], scalar_value=1),
        )
        resp = client.get("/api/team-members?itcode=user01")
        assert resp.status_code == 200
        reset_overrides()

    def test_name_filter(self):
        client = make_client(
            FakeResult([_MEMBER_ROW]),
            FakeResult([], scalar_value=1),
        )
        resp = client.get("/api/team-members?name=alice")
        assert resp.status_code == 200
        reset_overrides()

    def test_worker_type_filter(self):
        client = make_client(
            FakeResult([_MEMBER_ROW]),
            FakeResult([], scalar_value=1),
        )
        resp = client.get("/api/team-members?workerType=FTE")
        assert resp.status_code == 200
        reset_overrides()

    def test_country_filter(self):
        client = make_client(
            FakeResult([_MEMBER_ROW]),
            FakeResult([], scalar_value=1),
        )
        resp = client.get("/api/team-members?country=CN")
        assert resp.status_code == 200
        reset_overrides()

    def test_invalid_sort_field(self):
        client = make_client(
            FakeResult([_MEMBER_ROW]),
            FakeResult([], scalar_value=1),
        )
        resp = client.get("/api/team-members?sortField=badcol&sortOrder=desc")
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
        resp = client.get("/api/team-members")
        assert resp.status_code == 500
        reset_overrides()


class TestCreateTeamMember:
    def test_creates_member(self):
        client = make_client(FakeResult([_MEMBER_ROW]))
        resp = client.post("/api/team-members", json={"itcode": "user02", "name": "Bob"})
        assert resp.status_code in (200, 201)
        reset_overrides()

    def test_missing_itcode_returns_400(self):
        client = make_client(FakeResult([_MEMBER_ROW]))
        resp = client.post("/api/team-members", json={"name": "Bob"})
        assert resp.status_code == 400
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
        resp = client.post("/api/team-members", json={"itcode": "user02"})
        assert resp.status_code == 500
        reset_overrides()


class TestUpdateTeamMember:
    def test_updates_member(self):
        client = make_client(FakeResult([_MEMBER_ROW]))
        resp = client.put("/api/team-members/user01", json={"name": "Alice Updated"})
        assert resp.status_code == 200
        reset_overrides()

    def test_not_found_returns_404(self):
        client = make_client(FakeResult([]))  # mappings().first() → None
        resp = client.put("/api/team-members/notexist", json={"name": "X"})
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
        resp = client.put("/api/team-members/user01", json={"name": "X"})
        assert resp.status_code == 500
        reset_overrides()


class TestDeleteTeamMember:
    def test_deletes_member(self):
        from unittest.mock import AsyncMock, MagicMock
        from app.main import app
        from app.database import get_db
        from app.auth.dependencies import get_current_user
        from .conftest import override_current_user
        from fastapi.testclient import TestClient

        app.dependency_overrides[get_current_user] = override_current_user

        async def db_with_rowcount():
            db = AsyncMock()
            result = MagicMock()
            result.rowcount = 1
            db.execute = AsyncMock(return_value=result)
            db.commit = AsyncMock()
            yield db

        app.dependency_overrides[get_db] = db_with_rowcount
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.delete("/api/team-members/user01")
        assert resp.status_code == 200
        reset_overrides()

    def test_not_found_returns_404(self):
        from unittest.mock import AsyncMock, MagicMock
        from app.main import app
        from app.database import get_db
        from app.auth.dependencies import get_current_user
        from .conftest import override_current_user
        from fastapi.testclient import TestClient

        app.dependency_overrides[get_current_user] = override_current_user

        async def db_zero_rowcount():
            db = AsyncMock()
            result = MagicMock()
            result.rowcount = 0
            db.execute = AsyncMock(return_value=result)
            yield db

        app.dependency_overrides[get_db] = db_zero_rowcount
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.delete("/api/team-members/notexist")
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
        resp = client.delete("/api/team-members/user01")
        assert resp.status_code == 500
        reset_overrides()
