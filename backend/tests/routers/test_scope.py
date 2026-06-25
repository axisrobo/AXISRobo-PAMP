"""Tests for scope router."""
from __future__ import annotations

from .conftest import make_client, reset_overrides, FakeResult


_SCOPE_ROW = {
    "id": 1, "project_id": "P001", "scope_no": 1,
    "title": "Test Scope", "description": "Desc",
    "create_using_template": False, "sample": None,
}
_CHECKLIST_ROW = {
    "id": 1, "checklist_no": 1, "project_id": "P001",
    "category": "Security", "sub_category": "Auth",
    "questions": "Is auth enabled?", "answer": "Yes",
    "option": None, "comment": None, "link": None,
}
_TEMPLATE_ROW = {
    "id": 1, "title": "Template 1", "description": "Desc",
    "create_using_template": True, "sample": None,
}
_CHECKLIST_TEMPLATE_ROW = {
    "id": 1, "checklist_no": 1, "category": "Security",
    "sub_category": "Auth", "questions": "Q?", "answer": None,
    "option": None, "comment": None, "link": None,
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


class TestScopeOfChange:
    def test_list_no_filter(self):
        client = make_client(FakeResult([_SCOPE_ROW]))
        resp = client.get("/api/scope-of-change")
        assert resp.status_code == 200
        reset_overrides()

    def test_list_with_project_id(self):
        client = make_client(FakeResult([_SCOPE_ROW]))
        resp = client.get("/api/scope-of-change?projectId=P001")
        assert resp.status_code == 200
        reset_overrides()

    def test_list_with_request_id_found(self):
        # Two DB calls: lookup request, then scope list
        req_row = {"project_id": "P001"}
        client = make_client(
            FakeResult([req_row]),  # request lookup
            FakeResult([_SCOPE_ROW]),  # scope list
        )
        resp = client.get("/api/scope-of-change?requestId=EA001")
        assert resp.status_code == 200
        reset_overrides()

    def test_list_with_request_id_not_found(self):
        client = make_client(
            FakeResult([]),  # request not found
            FakeResult([]),  # empty scope list
        )
        resp = client.get("/api/scope-of-change?requestId=NOTEXIST")
        assert resp.status_code == 200
        reset_overrides()

    def test_create_scope(self):
        client = make_client(FakeResult([_SCOPE_ROW]))
        resp = client.post("/api/scope-of-change", json={
            "projectId": "P001", "title": "New Scope"
        })
        assert resp.status_code in (200, 201)
        reset_overrides()

    def test_update_scope(self):
        client = make_client(FakeResult([_SCOPE_ROW]))
        resp = client.put("/api/scope-of-change/1", json={"title": "Updated"})
        assert resp.status_code == 200
        reset_overrides()

    def test_update_scope_404(self):
        client = make_client(FakeResult([]))
        resp = client.put("/api/scope-of-change/999", json={"title": "X"})
        assert resp.status_code == 404
        reset_overrides()

    def test_delete_scope(self):
        from unittest.mock import AsyncMock, MagicMock
        from app.main import app
        from app.database import get_db
        from app.auth.dependencies import get_current_user
        from .conftest import override_current_user
        from fastapi.testclient import TestClient
        app.dependency_overrides[get_current_user] = override_current_user

        async def db_gen():
            db = AsyncMock()
            result = MagicMock()
            result.rowcount = 1
            db.execute = AsyncMock(return_value=result)
            db.commit = AsyncMock()
            yield db

        app.dependency_overrides[get_db] = db_gen
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.delete("/api/scope-of-change/1")
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
        resp = client.get("/api/scope-of-change")
        assert resp.status_code == 500
        reset_overrides()


class TestScopeChecklist:
    def test_list_checklist(self):
        client = make_client(FakeResult([_CHECKLIST_ROW]))
        resp = client.get("/api/scope-checklist?projectId=P001")
        assert resp.status_code == 200
        reset_overrides()

    def test_create_checklist(self):
        client = make_client(FakeResult([_CHECKLIST_ROW]))
        resp = client.post("/api/scope-checklist", json={
            "projectId": "P001", "category": "Security", "questions": "Q?"
        })
        assert resp.status_code in (200, 201)
        reset_overrides()

    def test_update_checklist(self):
        client = make_client(FakeResult([_CHECKLIST_ROW]))
        resp = client.put("/api/scope-checklist/1", json={"answer": "Yes"})
        assert resp.status_code == 200
        reset_overrides()

    def test_update_checklist_404(self):
        client = make_client(FakeResult([]))
        resp = client.put("/api/scope-checklist/999", json={"answer": "X"})
        assert resp.status_code == 404
        reset_overrides()


class TestScopeTemplates:
    def test_list_scope_templates(self):
        client = make_client(FakeResult([_TEMPLATE_ROW]))
        resp = client.get("/api/scope-templates")
        assert resp.status_code == 200
        reset_overrides()

    def test_list_checklist_templates(self):
        client = make_client(FakeResult([_CHECKLIST_TEMPLATE_ROW]))
        resp = client.get("/api/scope-checklist-templates")
        assert resp.status_code == 200
        reset_overrides()

    def test_list_scope_pages(self):
        client = make_client(FakeResult([_SCOPE_ROW]))
        resp = client.get("/api/scope-pages")
        assert resp.status_code == 200
        reset_overrides()
