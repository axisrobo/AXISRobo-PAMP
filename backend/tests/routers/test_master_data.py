"""Tests for master-data router."""
from __future__ import annotations

from datetime import datetime
from .conftest import make_client, reset_overrides, FakeResult


_CLASSIFICATION_ROW = {
    "id": 1, "method": "PII", "code": "L1", "name_zh": "个人",
    "name_en": "Personal", "parent": None, "sort": 1, "status": 1,
    "comment": None, "level": 1.0,
}
_DATA_CENTER_ROW = {
    "id": "dc-001", "name": "Beijing DC",
    "create_by": "admin", "create_at": datetime(2024, 1, 1),
}
_COMPANY_ROW = {
    "id": 1, "company_code": "CN01", "company_name": "Example Corp",
    "company_remark": None, "s4": "S4001", "area": "APAC",
}
_LEGAL_ENTITY_ROW = {
    "id": "le-001", "app_id": "11111111-1111-1111-1111-111111111111",
    "company_code": "CN01", "create_at": datetime(2024, 1, 1),
}
_HELP_FILE_ROW = {
    "id": 1, "usage": "guide", "file_name": "guide.pdf",
    "file_path": "/files/guide.pdf", "create_by": "admin",
    "create_at": datetime(2024, 1, 1),
}


class TestDataClassification:
    def test_returns_list(self):
        client = make_client(FakeResult([_CLASSIFICATION_ROW]))
        resp = client.get("/api/master-data/data-classification")
        assert resp.status_code == 200
        data = resp.json().get("data") or resp.json()
        assert isinstance(data, list)
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
        resp = client.get("/api/master-data/data-classification")
        assert resp.status_code == 500
        reset_overrides()


class TestDataCenters:
    def test_returns_list(self):
        client = make_client(FakeResult([_DATA_CENTER_ROW]))
        resp = client.get("/api/master-data/data-centers")
        assert resp.status_code == 200
        reset_overrides()


class TestCompanies:
    def test_returns_list(self):
        client = make_client(FakeResult([_COMPANY_ROW]))
        resp = client.get("/api/master-data/companies")
        assert resp.status_code == 200
        reset_overrides()

    def test_search_filter(self):
        client = make_client(FakeResult([_COMPANY_ROW]))
        resp = client.get("/api/master-data/companies?search=example")
        assert resp.status_code == 200
        reset_overrides()


class TestLegalEntities:
    def test_returns_list(self):
        client = make_client(FakeResult([_LEGAL_ENTITY_ROW]))
        resp = client.get("/api/master-data/legal-entities")
        assert resp.status_code == 200
        reset_overrides()

    def test_valid_app_id_filter(self):
        client = make_client(FakeResult([_LEGAL_ENTITY_ROW]))
        resp = client.get("/api/master-data/legal-entities?appId=11111111-1111-1111-1111-111111111111")
        assert resp.status_code == 200
        reset_overrides()

    def test_invalid_app_id_returns_empty(self):
        client = make_client(FakeResult([]))
        resp = client.get("/api/master-data/legal-entities?appId=not-a-uuid")
        assert resp.status_code == 200
        body = resp.json()
        data = body.get("data") if isinstance(body, dict) else body
        assert data == []
        reset_overrides()


class TestHelpFiles:
    def test_returns_list(self):
        client = make_client(FakeResult([_HELP_FILE_ROW]))
        resp = client.get("/api/master-data/help-files")
        assert resp.status_code == 200
        reset_overrides()
