"""Projects endpoint tests — Priority 2."""
import pytest
from helpers.pagination import assert_paginated, assert_has_keys


PROJECT_KEYS = [
    "id", "projectId", "name", "type", "status",
    "createdAt", "updatedAt",
]


@pytest.mark.readonly
@pytest.mark.priority2
class TestProjectsList:
    def test_list_paginated(self, client):
        resp = client.get("/api/projects")
        assert resp.status_code == 200
        body = resp.json()
        assert_paginated(body)

    def test_pagination_params(self, client):
        resp = client.get("/api/projects", params={"page": 1, "pageSize": 5})
        body = resp.json()
        assert len(body["data"]) <= 5

    def test_item_has_expected_keys(self, client):
        resp = client.get("/api/projects", params={"pageSize": 1})
        body = resp.json()
        if not body["data"]:
            pytest.skip("No projects")
        assert_has_keys(body["data"][0], PROJECT_KEYS, "project")

    def test_filter_projectId(self, client):
        sample = client.get("/api/projects", params={"pageSize": 1}).json()
        if not sample["data"]:
            pytest.skip("No projects")
        pid = sample["data"][0].get("projectId", "")
        if not pid:
            pytest.skip("No projectId")
        resp = client.get("/api/projects", params={"projectId": pid[:3]})
        assert resp.status_code == 200
        assert resp.json()["total"] > 0

    def test_filter_name(self, client):
        sample = client.get("/api/projects", params={"pageSize": 1}).json()
        if not sample["data"]:
            pytest.skip("No projects")
        name = sample["data"][0].get("name", "")
        if not name:
            pytest.skip("No name")
        resp = client.get("/api/projects", params={"name": name[:4]})
        assert resp.status_code == 200
        assert resp.json()["total"] > 0

    def test_filter_requestStatus(self, client):
        resp = client.get("/api/projects", params={"requestStatus": "Active"})
        assert resp.status_code == 200

    def test_filter_aiRelated(self, client):
        resp = client.get("/api/projects", params={"aiRelated": "Yes"})
        assert resp.status_code == 200

    def test_sort_by_name_asc(self, client):
        resp = client.get("/api/projects", params={
            "sortField": "name", "sortOrder": "asc", "pageSize": 20
        })
        assert resp.status_code == 200
        assert_paginated(resp.json())

    def test_sort_by_createdAt_desc(self, client):
        resp = client.get("/api/projects", params={
            "sortField": "createdAt", "sortOrder": "desc", "pageSize": 5
        })
        assert resp.status_code == 200

    def test_empty_result(self, client):
        resp = client.get("/api/projects", params={"projectId": "NONEXISTENT_XYZ_99999"})
        body = resp.json()
        assert body["total"] == 0
        assert body["data"] == []


@pytest.mark.readonly
@pytest.mark.priority2
class TestProjectsDetail:
    def test_get_by_id(self, client):
        sample = client.get("/api/projects", params={"pageSize": 1}).json()
        if not sample["data"]:
            pytest.skip("No projects")
        pid = sample["data"][0]["projectId"]
        resp = client.get(f"/api/projects/{pid}")
        assert resp.status_code == 200
        detail = resp.json()
        assert detail["projectId"] == pid

    def test_get_not_found(self, client):
        resp = client.get("/api/projects/NONEXISTENT_99999")
        assert resp.status_code in (404, 500)


@pytest.mark.write
@pytest.mark.priority2
class TestProjectsCRUD:
    def test_create_project(self, client):
        data = {
            "projectName": "__API_TEST_PROJECT__",
            "type": "Enhancement",
            "pm": "TESTPM",
            "pmItcode": "TESTPM",
            "dtLead": "TESTDT",
            "dtLeadItcode": "TESTDT",
            "itLead": "TESTIT",
            "itLeadItcode": "TESTIT",
            "source": "API Test",
            "createdBy": "api-test",
        }
        resp = client.post("/api/projects", json=data)
        assert resp.status_code == 201
        created = resp.json()
        assert created["name"] == "__API_TEST_PROJECT__"
        assert "projectId" in created

    def test_update_project(self, client):
        # Find the test project we created
        resp = client.get("/api/projects", params={"name": "__API_TEST_PROJECT__"})
        body = resp.json()
        if not body["data"]:
            pytest.skip("Test project not found")
        pid = body["data"][0]["projectId"]
        update_resp = client.put(f"/api/projects/{pid}", json={
            "comment": "Updated by API test",
            "updatedBy": "api-test",
        })
        assert update_resp.status_code == 200
