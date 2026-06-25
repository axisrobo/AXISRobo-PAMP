"""Business Capability Master Data endpoint tests — Priority 1."""
import pytest
from helpers.pagination import assert_paginated, assert_has_keys

BIZ_CAPABILITY_KEYS = [
    "id", "bcId", "bcName", "level", "version", "domainL1", "subDomainL2",
]


@pytest.mark.readonly
@pytest.mark.priority1
class TestBizCapabilityList:
    def test_list_paginated(self, client):
        resp = client.get("/api/biz-capability")
        assert resp.status_code == 200
        body = resp.json()
        assert_paginated(body, min_total=1)
        assert_has_keys(body["data"][0], BIZ_CAPABILITY_KEYS, "bizCapability item")

    def test_pagination_params(self, client):
        resp = client.get("/api/biz-capability", params={"page": 2, "pageSize": 5})
        body = resp.json()
        assert body["page"] == 2
        assert len(body["data"]) <= 5

    def test_filter_version(self, client):
        sample = client.get("/api/biz-capability", params={"pageSize": 1}).json()["data"][0]
        version = sample.get("version")
        if not version:
            pytest.skip("No version")
        resp = client.get("/api/biz-capability", params={"version": version})
        body = resp.json()
        assert body["total"] > 0
        for item in body["data"]:
            assert item["version"] == version

    def test_filter_domainL1(self, client):
        sample = client.get("/api/biz-capability", params={"pageSize": 1}).json()["data"][0]
        domain = sample.get("domainL1")
        if not domain:
            pytest.skip("No domainL1")
        resp = client.get("/api/biz-capability", params={"domainL1": domain})
        body = resp.json()
        assert body["total"] > 0

    def test_filter_bcName(self, client):
        sample = client.get("/api/biz-capability", params={"pageSize": 1}).json()["data"][0]
        name = sample.get("bcName", "")
        if not name:
            pytest.skip("No bcName")
        resp = client.get("/api/biz-capability", params={"bcName": name[:4]})
        body = resp.json()
        assert body["total"] > 0

    def test_filter_level(self, client):
        resp = client.get("/api/biz-capability", params={"level": 3})
        body = resp.json()
        for item in body["data"]:
            assert item["level"] == 3

    def test_sort_by_bcId_asc(self, client):
        resp = client.get("/api/biz-capability", params={"sortField": "bcId", "sortOrder": "asc", "pageSize": 10})
        assert resp.status_code == 200
        assert_paginated(resp.json())

    def test_sort_by_bcName_desc(self, client):
        resp = client.get("/api/biz-capability", params={"sortField": "bcName", "sortOrder": "desc", "pageSize": 10})
        assert resp.status_code == 200

    def test_empty_filter(self, client):
        resp = client.get("/api/biz-capability", params={"bcName": "NONEXISTENT_XYZ_99999"})
        body = resp.json()
        assert body["total"] == 0
