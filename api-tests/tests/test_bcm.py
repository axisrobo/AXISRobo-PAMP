"""BCM (Business Capability Mapping) endpoint tests — Priority 1."""
import pytest
from helpers.pagination import assert_paginated, assert_has_keys


@pytest.mark.readonly
@pytest.mark.priority1
class TestBcmList:
    def test_list_paginated(self, client):
        resp = client.get("/api/applications/bcm")
        assert resp.status_code == 200
        body = resp.json()
        assert_paginated(body, min_total=1)
        expected_keys = ["id", "appId", "appName", "bcId", "bcName", "domainL1", "subDomainL2", "version"]
        assert_has_keys(body["data"][0], expected_keys, "bcm item")

    def test_pagination(self, client):
        resp = client.get("/api/applications/bcm", params={"page": 1, "pageSize": 5})
        body = resp.json()
        assert len(body["data"]) <= 5

    def test_filter_appId(self, client):
        sample = client.get("/api/applications/bcm", params={"pageSize": 1}).json()["data"][0]
        app_id = sample.get("appId")
        if not app_id:
            pytest.skip("No appId")
        resp = client.get("/api/applications/bcm", params={"appId": app_id[:3]})
        body = resp.json()
        assert body["total"] > 0

    def test_filter_domainL1(self, client):
        sample = client.get("/api/applications/bcm", params={"pageSize": 1}).json()["data"][0]
        domain = sample.get("domainL1")
        if not domain:
            pytest.skip("No domainL1")
        resp = client.get("/api/applications/bcm", params={"domainL1": domain[:5]})
        body = resp.json()
        assert body["total"] > 0

    def test_filter_bcName(self, client):
        sample = client.get("/api/applications/bcm", params={"pageSize": 1}).json()["data"][0]
        bc_name = sample.get("bcName")
        if not bc_name:
            pytest.skip("No bcName")
        resp = client.get("/api/applications/bcm", params={"bcName": bc_name[:4]})
        body = resp.json()
        assert body["total"] > 0

    def test_empty_result(self, client):
        resp = client.get("/api/applications/bcm", params={"appId": "NONEXISTENT_XYZ_99999"})
        body = resp.json()
        assert body["total"] == 0
        assert body["data"] == []


@pytest.mark.readonly
@pytest.mark.priority1
class TestBcmVersions:
    def test_versions_returns_list(self, client):
        resp = client.get("/api/applications/bcm/versions")
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)


@pytest.mark.readonly
@pytest.mark.priority1
class TestBcmBcTree:
    def test_bc_tree_returns_list(self, client):
        resp = client.get("/api/applications/bcm/bc-tree")
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)
        if body:
            assert_has_keys(body[0], ["id", "bcId", "bcName", "level"], "bc-tree item")

    def test_bc_tree_search(self, client):
        resp = client.get("/api/applications/bcm/bc-tree", params={"q": "IT"})
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)


@pytest.mark.readonly
@pytest.mark.priority1
class TestBcmVisualization:
    def test_viz_returns_expected_shape(self, client):
        resp = client.get("/api/applications/bcm/visualization")
        assert resp.status_code == 200
        body = resp.json()
        assert "capabilities" in body and isinstance(body["capabilities"], list)
        assert "applications" in body and isinstance(body["applications"], list)
        assert "mappings" in body and isinstance(body["mappings"], list)
        assert "domains" in body and isinstance(body["domains"], list)
        assert "dataVersion" in body

    def test_viz_capabilities_structure(self, client):
        resp = client.get("/api/applications/bcm/visualization")
        body = resp.json()
        if body["capabilities"]:
            cap = body["capabilities"][0]
            assert_has_keys(cap, ["id", "name", "level"], "capability")

    def test_viz_applications_structure(self, client):
        resp = client.get("/api/applications/bcm/visualization")
        body = resp.json()
        if body["applications"]:
            app = body["applications"][0]
            assert_has_keys(app, ["appId", "appName"], "application")

    def test_viz_mappings_structure(self, client):
        resp = client.get("/api/applications/bcm/visualization")
        body = resp.json()
        if body["mappings"]:
            m = body["mappings"][0]
            assert_has_keys(m, ["appId", "bcId"], "mapping")
