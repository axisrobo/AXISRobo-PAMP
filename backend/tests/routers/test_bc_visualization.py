"""Tests for BC Visualization router."""
from __future__ import annotations

from .conftest import make_client, reset_overrides, FakeResult


_BCM_ROW = {
    "app_id": "APP001",
    "app_name": "App One",
    "app_full_name": "Application One",
    "app_ownership": "IT",
    "app_solution_owner": "user01",
    "app_it_owner": "user01",
    "portfolio_mgt": "EA",
    "app_solution_type": "SaaS",
    "app_classification": "Business",
    "app_status": "Active",
    "biz_function": "Finance",
    "owned_by": "user01",
    "app_owner_tower": "EA",
    "app_owner_domain": "Finance",
    "app_dt_owner": "user01",
    "app_description": "Desc",
    "geo": "APAC",
    "actual_k": None,
    "bc_id": "BC001",
    "bc_name": "Finance BC",
    "bc_name_cn": "\u8d22\u52a1",
    "lv1_domain": "Finance",
    "lv2_sub_domain": "Accounting",
    "lv3_capability_group": "AP",
    "parent_bc_id": "",
    "bc_description": "BC Desc",
    "bc_level": 3,
    "data_version": "2025Q1",
}


class TestBCVisualization:
    def test_returns_data(self):
        client = make_client(FakeResult([_BCM_ROW]))
        resp = client.get("/api/applications/bcm/visualization")
        assert resp.status_code == 200
        reset_overrides()

    def test_version_filter(self):
        client = make_client(FakeResult([_BCM_ROW]))
        resp = client.get("/api/applications/bcm/visualization?version=2025Q1")
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
        resp = client.get("/api/applications/bcm/visualization")
        assert resp.status_code == 500
        reset_overrides()
