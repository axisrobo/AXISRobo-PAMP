"""Resources endpoint tests — Priority 3."""
import pytest
from helpers.pagination import assert_paginated, assert_has_keys


@pytest.mark.readonly
@pytest.mark.priority3
class TestResourcesList:
    def test_list_paginated(self, client):
        resp = client.get("/api/resources")
        assert resp.status_code == 200
        body = resp.json()
        assert_paginated(body)

    def test_item_keys(self, client):
        resp = client.get("/api/resources", params={"pageSize": 1})
        body = resp.json()
        if not body["data"]:
            pytest.skip("No resources")
        assert_has_keys(body["data"][0], ["itcode", "name"], "resource")

    def test_filter_itcode(self, client):
        resp = client.get("/api/resources", params={"itcode": "A"})
        assert resp.status_code == 200

    def test_filter_name(self, client):
        resp = client.get("/api/resources", params={"name": "a"})
        assert resp.status_code == 200

    def test_filter_country(self, client):
        resp = client.get("/api/resources", params={"country": "CN"})
        assert resp.status_code == 200

    def test_filter_tier1Org(self, client):
        resp = client.get("/api/resources", params={"tier1Org": "DT"})
        assert resp.status_code == 200

    def test_pagination_size(self, client):
        resp = client.get("/api/resources", params={"page": 1, "pageSize": 3})
        body = resp.json()
        assert len(body["data"]) <= 3


@pytest.mark.readonly
@pytest.mark.priority3
class TestResourcesSearch:
    def test_search(self, client):
        resp = client.get("/api/resources/search", params={"q": "test"})
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list)
        assert len(body) <= 20

    def test_search_too_short(self, client):
        resp = client.get("/api/resources/search", params={"q": "a"})
        # Should return 400 or empty (min 2 chars)
        assert resp.status_code in (200, 400)
