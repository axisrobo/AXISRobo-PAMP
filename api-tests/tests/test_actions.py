"""Actions endpoint tests — Priority 2."""
import pytest
from helpers.pagination import assert_paginated, assert_has_keys


ACTION_KEYS = ["id", "actionNo", "title", "projectId", "status", "priority"]


@pytest.mark.readonly
@pytest.mark.priority2
class TestActionsList:
    def test_list_paginated(self, client):
        resp = client.get("/api/actions")
        assert resp.status_code == 200
        body = resp.json()
        assert_paginated(body)

    def test_has_stats(self, client):
        resp = client.get("/api/actions")
        body = resp.json()
        assert "stats" in body
        stats = body["stats"]
        for key in ["total", "open", "inValidation", "closed"]:
            assert key in stats, f"Missing stats key: {key}"

    def test_pagination_params(self, client):
        resp = client.get("/api/actions", params={"page": 1, "pageSize": 5})
        body = resp.json()
        assert len(body["data"]) <= 5

    def test_item_keys(self, client):
        resp = client.get("/api/actions", params={"pageSize": 1})
        body = resp.json()
        if not body["data"]:
            pytest.skip("No actions")
        assert_has_keys(body["data"][0], ACTION_KEYS, "action")

    def test_filter_title(self, client):
        resp = client.get("/api/actions", params={"title": "review"})
        assert resp.status_code == 200

    def test_filter_status(self, client):
        resp = client.get("/api/actions", params={"status": "Open"})
        assert resp.status_code == 200

    def test_filter_priority(self, client):
        resp = client.get("/api/actions", params={"priority": "High"})
        assert resp.status_code == 200

    def test_filter_projectId(self, client):
        sample = client.get("/api/actions", params={"pageSize": 1}).json()
        if not sample["data"]:
            pytest.skip("No actions")
        pid = sample["data"][0].get("projectId", "")
        if not pid:
            pytest.skip("No projectId")
        resp = client.get("/api/actions", params={"projectId": pid})
        assert resp.status_code == 200
        assert resp.json()["total"] > 0

    def test_sort_by_createdAt(self, client):
        resp = client.get("/api/actions", params={
            "sortField": "createdAt", "sortOrder": "desc"
        })
        assert resp.status_code == 200

    def test_empty_result(self, client):
        resp = client.get("/api/actions", params={"projectId": "NONEXISTENT_XYZ_99999"})
        body = resp.json()
        assert body["total"] == 0
        assert body["data"] == []


@pytest.mark.readonly
@pytest.mark.priority2
class TestActionsDetail:
    def test_get_by_actionNo(self, client):
        sample = client.get("/api/actions", params={"pageSize": 1}).json()
        if not sample["data"]:
            pytest.skip("No actions")
        action_no = sample["data"][0]["actionNo"]
        resp = client.get(f"/api/actions/{action_no}")
        assert resp.status_code == 200
        detail = resp.json()
        assert detail["actionNo"] == action_no

    def test_get_not_found(self, client):
        resp = client.get("/api/actions/999999")
        assert resp.status_code in (404, 500)


@pytest.mark.write
@pytest.mark.priority2
class TestActionsCRUD:
    def test_create_update_delete(self, client):
        projects = client.get("/api/projects", params={"pageSize": 1}).json()
        if not projects["data"]:
            pytest.skip("No projects")
        pid = projects["data"][0]["projectId"]

        # Create
        create_data = {
            "projectId": pid,
            "actionTitle": "__API_TEST_ACTION__",
            "priority": "Medium",
            "actionDescription": "Created by API test",
            "type": "Action",
            "requestedBy": "TESTUSER",
            "requestedByName": "Test User",
            "applicableDomain": "Test Domain",
            "createdBy": "api-test",
        }
        resp = client.post("/api/actions", json=create_data)
        assert resp.status_code == 201
        created = resp.json()
        action_no = created["actionNo"]

        # Update
        update_resp = client.put(f"/api/actions/{action_no}", json={
            "actionDescription": "Updated by API test",
            "updatedBy": "api-test",
        })
        assert update_resp.status_code == 200

        # Delete (hard delete)
        del_resp = client.delete(f"/api/actions/{action_no}")
        assert del_resp.status_code == 200
