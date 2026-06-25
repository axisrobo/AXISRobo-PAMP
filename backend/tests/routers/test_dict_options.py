"""Tests for GET /api/dict-options and /api/dict-options/categories."""
from __future__ import annotations

from .conftest import make_client, reset_overrides, FakeResult


_OPTION_ROW = {
    "category_id": 1,
    "option_id": 10,
    "option": "Active",
    "lang": "en",
    "description": "Active status",
    "status": 1,
}

_CATEGORY_ROW = {
    "category_id": 1,
    "description": "Status",
}


class TestGetDictOptions:
    def setup_method(self):
        self.client = make_client(FakeResult([_OPTION_ROW]))

    def teardown_method(self):
        reset_overrides()

    def test_returns_list(self):
        resp = self.client.get("/api/dict-options")
        assert resp.status_code == 200
        data = resp.json().get("data") or resp.json()
        assert isinstance(data, list)
        assert data[0]["categoryId"] == 1

    def test_filter_by_category_id(self):
        resp = self.client.get("/api/dict-options?categoryId=1")
        assert resp.status_code == 200

    def test_filter_by_lang(self):
        resp = self.client.get("/api/dict-options?lang=zh")
        assert resp.status_code == 200

    def test_db_error_returns_500(self):
        from unittest.mock import AsyncMock
        from app.main import app
        from app.database import get_db
        from app.auth.dependencies import get_current_user
        from .conftest import override_current_user

        app.dependency_overrides[get_current_user] = override_current_user

        async def bad_db():
            db = AsyncMock()
            async def _raise(*a, **kw):
                raise RuntimeError("DB error")
            db.execute = _raise
            yield db

        app.dependency_overrides[get_db] = bad_db
        from fastapi.testclient import TestClient
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/api/dict-options")
        assert resp.status_code == 500
        reset_overrides()


class TestGetCategories:
    def setup_method(self):
        self.client = make_client(FakeResult([_CATEGORY_ROW]))

    def teardown_method(self):
        reset_overrides()

    def test_returns_categories(self):
        resp = self.client.get("/api/dict-options/categories")
        assert resp.status_code == 200
        data = resp.json().get("data") or resp.json()
        assert isinstance(data, list)
        assert data[0]["categoryId"] == 1

    def test_db_error_returns_500(self):
        from unittest.mock import AsyncMock
        from app.main import app
        from app.database import get_db
        from app.auth.dependencies import get_current_user
        from .conftest import override_current_user

        app.dependency_overrides[get_current_user] = override_current_user

        async def bad_db():
            db = AsyncMock()
            async def _raise(*a, **kw):
                raise RuntimeError("DB error")
            db.execute = _raise
            yield db

        app.dependency_overrides[get_db] = bad_db
        from fastapi.testclient import TestClient
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/api/dict-options/categories")
        assert resp.status_code == 500
        reset_overrides()
