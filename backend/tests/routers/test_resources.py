"""Tests for resources router."""
from __future__ import annotations

from .conftest import make_client, reset_overrides, FakeResult


_RESOURCE_ROW = {
    "itcode": "user01",
    "name": "Alice Smith",
    "email": "alice@example.com",
    "worker": "FTE",
    "worker_type": "FTE",
    "country": "CN",
    "location": "Beijing",
    "tier_1_org": "IT",
    "tier_2_org": "EA",
    "tier_3_org": "Dev",
}


class TestSearchResources:
    def test_search_with_query(self):
        client = make_client(FakeResult([_RESOURCE_ROW]))
        resp = client.get("/api/resources/search?q=alice")
        assert resp.status_code == 200
        data = resp.json().get("data") or resp.json()
        assert isinstance(data, list)
        reset_overrides()

    def test_search_without_query(self):
        client = make_client(FakeResult([_RESOURCE_ROW]))
        resp = client.get("/api/resources/search")
        assert resp.status_code == 200
        reset_overrides()

    def test_search_with_limit(self):
        client = make_client(FakeResult([_RESOURCE_ROW]))
        resp = client.get("/api/resources/search?limit=10")
        assert resp.status_code == 200
        reset_overrides()

    def test_search_db_error_returns_500(self):
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
                raise RuntimeError("fail")
            db.execute = _raise
            yield db

        app.dependency_overrides[get_db] = bad_db
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/api/resources/search?q=test")
        assert resp.status_code == 500
        reset_overrides()


class TestListResources:
    def test_returns_paginated(self):
        client = make_client(
            FakeResult([_RESOURCE_ROW]),
            FakeResult([], scalar_value=1),
        )
        resp = client.get("/api/resources")
        assert resp.status_code == 200
        reset_overrides()

    def test_itcode_filter(self):
        client = make_client(
            FakeResult([_RESOURCE_ROW]),
            FakeResult([], scalar_value=1),
        )
        resp = client.get("/api/resources?itcode=user01")
        assert resp.status_code == 200
        reset_overrides()

    def test_name_filter(self):
        client = make_client(
            FakeResult([_RESOURCE_ROW]),
            FakeResult([], scalar_value=1),
        )
        resp = client.get("/api/resources?name=alice")
        assert resp.status_code == 200
        reset_overrides()

    def test_country_filter(self):
        client = make_client(
            FakeResult([_RESOURCE_ROW]),
            FakeResult([], scalar_value=1),
        )
        resp = client.get("/api/resources?country=CN")
        assert resp.status_code == 200
        reset_overrides()

    def test_tier1org_filter(self):
        client = make_client(
            FakeResult([_RESOURCE_ROW]),
            FakeResult([], scalar_value=1),
        )
        resp = client.get("/api/resources?tier1Org=IT")
        assert resp.status_code == 200
        reset_overrides()

    def test_sort_desc(self):
        client = make_client(
            FakeResult([_RESOURCE_ROW]),
            FakeResult([], scalar_value=1),
        )
        resp = client.get("/api/resources?sortField=name&sortOrder=desc")
        assert resp.status_code == 200
        reset_overrides()

    def test_invalid_sort_field(self):
        client = make_client(
            FakeResult([_RESOURCE_ROW]),
            FakeResult([], scalar_value=1),
        )
        resp = client.get("/api/resources?sortField=badcol")
        assert resp.status_code == 200
        reset_overrides()

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
                raise RuntimeError("fail")
            db.execute = _raise
            yield db

        app.dependency_overrides[get_db] = bad_db
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/api/resources")
        assert resp.status_code == 500
        reset_overrides()
