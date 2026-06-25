"""EA Requests endpoint tests — Priority 2."""
import pytest
from helpers.pagination import assert_paginated, assert_has_keys


@pytest.mark.readonly
@pytest.mark.priority2
class TestEaRequestsList:
    def test_list_paginated(self, client):
        resp = client.get("/api/ea-requests")
        assert resp.status_code == 200
        body = resp.json()
        assert_paginated(body)

    def test_pagination_params(self, client):
        resp = client.get("/api/ea-requests", params={"page": 1, "pageSize": 5})
        body = resp.json()
        assert len(body["data"]) <= 5

    def test_item_keys(self, client):
        resp = client.get("/api/ea-requests", params={"pageSize": 1})
        body = resp.json()
        if not body["data"]:
            pytest.skip("No ea-requests")
        expected = ["id", "requestId", "projectId", "status"]
        assert_has_keys(body["data"][0], expected, "ea-request")

    def test_filter_requestId(self, client):
        sample = client.get("/api/ea-requests", params={"pageSize": 1}).json()
        if not sample["data"]:
            pytest.skip("No ea-requests")
        rid = sample["data"][0].get("requestId", "")
        if not rid:
            pytest.skip("No requestId")
        resp = client.get("/api/ea-requests", params={"requestId": rid[:4]})
        assert resp.status_code == 200
        assert resp.json()["total"] > 0

    def test_filter_status(self, client):
        resp = client.get("/api/ea-requests", params={"status": "Completed"})
        assert resp.status_code == 200

    def test_filter_reviewResult(self, client):
        resp = client.get("/api/ea-requests", params={"reviewResult": "Approved"})
        assert resp.status_code == 200

    def test_filter_reviewResult_exception_alias(self, client):
        resp = client.get("/api/ea-requests", params={"reviewResult": "Approved with Exception"})
        assert resp.status_code == 200

    def test_filter_scope(self, client):
        resp = client.get("/api/ea-requests", params={"scope": "Full"})
        assert resp.status_code == 200

    def test_filter_projectName(self, client):
        resp = client.get("/api/ea-requests", params={"projectName": "test"})
        assert resp.status_code == 200

    def test_filter_projectId_exact_match(self, client):
        sample = client.get("/api/ea-requests", params={"pageSize": 1}).json()
        if not sample["data"]:
            pytest.skip("No ea-requests")
        project_id = sample["data"][0].get("projectId", "")
        if not project_id:
            pytest.skip("No projectId")
        resp = client.get("/api/ea-requests", params={"projectId": project_id})
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] > 0
        assert all(item.get("projectId") == project_id for item in body["data"])

    def test_filter_organization(self, client):
        resp = client.get("/api/ea-requests", params={"organization": "DTIT"})
        assert resp.status_code == 200

    def test_filter_dateRange(self, client):
        resp = client.get("/api/ea-requests", params={
            "dateFrom": "2024-01-01", "dateTo": "2025-12-31"
        })
        assert resp.status_code == 200

    def test_sort_by_createdAt(self, client):
        resp = client.get("/api/ea-requests", params={
            "sortField": "createdAt", "sortOrder": "desc", "pageSize": 10
        })
        assert resp.status_code == 200

    def test_empty_result(self, client):
        resp = client.get("/api/ea-requests", params={"requestId": "NONEXISTENT_XYZ_99999"})
        body = resp.json()
        assert body["total"] == 0
        assert body["data"] == []


@pytest.mark.readonly
@pytest.mark.priority2
class TestEaRequestsDetail:
    def test_get_by_requestId(self, client):
        sample = client.get("/api/ea-requests", params={"pageSize": 1}).json()
        if not sample["data"]:
            pytest.skip("No ea-requests")
        request_id = sample["data"][0]["requestId"]
        resp = client.get(f"/api/ea-requests/{request_id}")
        assert resp.status_code == 200
        detail = resp.json()
        assert detail["requestId"] == request_id

    def test_get_not_found(self, client):
        resp = client.get("/api/ea-requests/999999")
        assert resp.status_code in (404, 500)


@pytest.mark.readonly
@pytest.mark.priority2
class TestEaRequestsDashboard:
    def test_dashboard_returns_object(self, client):
        resp = client.get("/api/ea-requests/dashboard")
        assert resp.status_code == 200
        body = resp.json()
        expected = ["statusCounts", "completedResultCounts"]
        for key in expected:
            assert key in body, f"Missing dashboard key: {key}"

    def test_dashboard_with_date_filter(self, client):
        resp = client.get("/api/ea-requests/dashboard", params={
            "from": "2024-01-01", "to": "2025-12-31"
        })
        assert resp.status_code == 200

    def test_dashboard_with_org_filter(self, client):
        resp = client.get("/api/ea-requests/dashboard", params={"org": "DTIT"})
        assert resp.status_code == 200


@pytest.mark.readonly
@pytest.mark.priority2
class TestEaRequestsFilterOptions:
    def test_filter_options_returns_data(self, client):
        resp = client.get("/api/ea-requests/filter-options")
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, dict)
        assert "projects" in body
        assert "organizations" in body
        if body["projects"]:
            first_project = body["projects"][0]
            assert "project_id" in first_project
            assert "project_name" in first_project


@pytest.mark.write
@pytest.mark.priority2
class TestEaRequestsCRUD:
    def test_create_and_soft_delete(self, client):
        # Need a project first
        projects = client.get("/api/projects", params={"pageSize": 1}).json()
        if not projects["data"]:
            pytest.skip("No projects for linking")
        pid = projects["data"][0]["projectId"]
        create_data = {
            "projectId": pid,
            "reviewScope": "Full Review",
            "requester": "API Test",
            "organization": "DTIT",
            "requestDesc": "API test request",
            "createdBy": "api-test",
        }
        resp = client.post("/api/ea-requests", json=create_data)
        assert resp.status_code == 201
        created = resp.json()
        assert "requestId" in created
        req_id = created["requestId"]

        # Soft delete
        del_resp = client.delete(f"/api/ea-requests/{req_id}")
        assert del_resp.status_code == 200

    def test_update_request(self, client):
        # Create then update
        projects = client.get("/api/projects", params={"pageSize": 1}).json()
        if not projects["data"]:
            pytest.skip("No projects")
        pid = projects["data"][0]["projectId"]
        created = client.post("/api/ea-requests", json={
            "projectId": pid,
            "reviewScope": "Quick Review",
            "requester": "API Test Update",
            "createdBy": "api-test",
        }).json()
        req_id = created["requestId"]

        update_resp = client.put(f"/api/ea-requests/{req_id}", json={
            "requestDesc": "Updated by API test",
            "updatedBy": "api-test",
        })
        assert update_resp.status_code == 200

        # Cleanup
        client.delete(f"/api/ea-requests/{req_id}")
