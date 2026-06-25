"""Scope of Change & Checklist endpoint tests — Priority 3."""
import pytest


@pytest.mark.readonly
@pytest.mark.priority3
class TestScopeOfChange:
    def test_list_returns_array(self, client):
        resp = client.get("/api/scope-of-change")
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)

    def test_filter_projectId(self, client):
        resp = client.get("/api/scope-of-change", params={"projectId": "P001"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_filter_requestId(self, client):
        resp = client.get("/api/scope-of-change", params={"requestId": "EA250001"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


@pytest.mark.readonly
@pytest.mark.priority3
class TestScopeOfChangeTemplates:
    def test_templates_returns_array(self, client):
        resp = client.get("/api/scope-of-change-templates")
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)


@pytest.mark.readonly
@pytest.mark.priority3
class TestScopeCheckList:
    def test_list_returns_array(self, client):
        resp = client.get("/api/scope-check-list")
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)

    def test_filter_projectId(self, client):
        resp = client.get("/api/scope-check-list", params={"projectId": "P001"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


@pytest.mark.readonly
@pytest.mark.priority3
class TestScopeCheckListTemplates:
    def test_templates_returns_array(self, client):
        resp = client.get("/api/scope-check-list-templates")
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)


@pytest.mark.write
@pytest.mark.priority3
class TestScopeCRUD:
    def test_create_and_delete_scope(self, client):
        # Need a project
        projects = client.get("/api/projects", params={"pageSize": 1}).json()
        if not projects["data"]:
            pytest.skip("No projects")
        pid = projects["data"][0]["projectId"]

        data = {
            "projectId": pid,
            "title": "__API_TEST_SCOPE__",
            "description": "Created by API test",
        }
        resp = client.post("/api/scope-of-change", json=data)
        assert resp.status_code == 201
        created = resp.json()
        scope_id = created["id"]

        # Get pages
        pages_resp = client.get(f"/api/scope-of-change/{scope_id}/pages")
        assert pages_resp.status_code == 200
        assert isinstance(pages_resp.json(), list)

        # Update
        update_resp = client.put(f"/api/scope-of-change/{scope_id}", json={
            "title": "__API_TEST_SCOPE_UPDATED__",
        })
        assert update_resp.status_code == 200

        # Delete
        del_resp = client.delete(f"/api/scope-of-change/{scope_id}")
        assert del_resp.status_code == 200

    def test_create_and_update_checklist(self, client):
        projects = client.get("/api/projects", params={"pageSize": 1}).json()
        if not projects["data"]:
            pytest.skip("No projects")
        pid = projects["data"][0]["projectId"]

        data = {
            "projectId": pid,
            "checklistNo": 9999,
            "category": "API Test Category",
            "questions": "Is this a test?",
            "answer": "Yes",
        }
        resp = client.post("/api/scope-check-list", json=data)
        assert resp.status_code == 201
        created = resp.json()
        checklist_id = created["id"]

        # Update
        update_resp = client.put(f"/api/scope-check-list/{checklist_id}", json={
            "answer": "Updated",
        })
        assert update_resp.status_code == 200
