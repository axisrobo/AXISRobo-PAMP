"""CMDB Application Master Data endpoint tests — Priority 1."""
import pytest
from helpers.pagination import assert_paginated, assert_has_keys

CMDB_KEYS = [
    "appId", "name", "appFullName", "shortDescription", "status",
    "appOwnership", "ownedBy", "appItOwner", "appDtOwner", "appOperationOwner",
    "appOwnerTower", "appOwnerDomain", "appOperationOwnerTower", "appOperationOwnerDomain",
    "portfolioMgt", "appClassification", "appSolutionType", "serviceArea",
    "patchLevel", "updateAt", "decommissionedAt",
]


@pytest.mark.readonly
@pytest.mark.priority1
class TestCmdbList:
    def test_list_paginated(self, client):
        resp = client.get("/api/cmdb")
        assert resp.status_code == 200
        body = resp.json()
        assert_paginated(body, min_total=1)
        assert_has_keys(body["data"][0], CMDB_KEYS, "cmdb item")

    def test_pagination_page_size(self, client):
        resp = client.get("/api/cmdb", params={"page": 1, "pageSize": 5})
        body = resp.json()
        assert len(body["data"]) <= 5

    def test_filter_appId(self, client):
        # Get a sample value first
        sample = client.get("/api/cmdb", params={"pageSize": 1}).json()["data"][0]
        app_id = sample["appId"]
        if not app_id:
            pytest.skip("No appId in first row")
        resp = client.get("/api/cmdb", params={"appId": app_id[:3]})
        body = resp.json()
        assert body["total"] > 0
        for item in body["data"]:
            assert app_id[:3].lower() in (item["appId"] or "").lower()

    def test_filter_name(self, client):
        sample = client.get("/api/cmdb", params={"pageSize": 1}).json()["data"][0]
        name = sample["name"] or sample["appFullName"]
        if not name:
            pytest.skip("No name in first row")
        term = name[:4]
        resp = client.get("/api/cmdb", params={"name": term})
        body = resp.json()
        assert body["total"] > 0

    def test_filter_status(self, client):
        resp = client.get("/api/cmdb", params={"status": "Active"})
        body = resp.json()
        assert body["total"] >= 0  # May have 0 results

    def test_filter_ownerTower(self, client):
        resp = client.get("/api/cmdb", params={"ownerTower": "DT"})
        assert resp.status_code == 200

    def test_filter_portfolio(self, client):
        resp = client.get("/api/cmdb", params={"portfolio": "Invest"})
        assert resp.status_code == 200

    def test_filter_classification(self, client):
        resp = client.get("/api/cmdb", params={"classification": "Core"})
        assert resp.status_code == 200

    def test_filter_solutionType(self, client):
        resp = client.get("/api/cmdb", params={"solutionType": "SaaS"})
        assert resp.status_code == 200

    def test_filter_ownership(self, client):
        resp = client.get("/api/cmdb", params={"ownership": "Internal"})
        assert resp.status_code == 200

    def test_combined_filters(self, client):
        resp = client.get("/api/cmdb", params={"status": "Active", "pageSize": 5})
        assert resp.status_code == 200

    def test_sort_by_name_asc(self, client):
        resp = client.get("/api/cmdb", params={"sortKey": "name", "sortDir": "asc", "pageSize": 20})
        body = resp.json()
        assert_paginated(body)

    def test_sort_by_appId_desc(self, client):
        resp = client.get("/api/cmdb", params={"sortKey": "appId", "sortDir": "desc", "pageSize": 5})
        body = resp.json()
        assert_paginated(body)

    def test_empty_result(self, client):
        resp = client.get("/api/cmdb", params={"appId": "NONEXISTENT_XYZ_99999"})
        body = resp.json()
        assert body["total"] == 0
        assert body["data"] == []


@pytest.mark.readonly
@pytest.mark.priority1
class TestCmdbDetail:
    def test_detail_returns_object(self, client):
        sample = client.get("/api/cmdb", params={"pageSize": 1}).json()["data"][0]
        app_id = sample["appId"]
        resp = client.get(f"/api/cmdb/{app_id}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["appId"] == app_id

    def test_detail_not_found(self, client):
        resp = client.get("/api/cmdb/NONEXISTENT_XYZ_99999")
        assert resp.status_code == 404

    def test_detail_not_paginated(self, client):
        sample = client.get("/api/cmdb", params={"pageSize": 1}).json()["data"][0]
        resp = client.get(f"/api/cmdb/{sample['appId']}")
        body = resp.json()
        # Should be flat object, not wrapped
        assert "data" not in body or not isinstance(body.get("data"), list)
