"""Technology Stack endpoint tests — Priority 3."""
import pytest
from helpers.pagination import assert_paginated, assert_has_keys


@pytest.mark.readonly
@pytest.mark.priority3
class TestTechnologyStack:
    def test_list_paginated(self, client):
        resp = client.get("/api/technology-stack")
        assert resp.status_code == 200
        body = resp.json()
        assert_paginated(body)

    def test_item_keys(self, client):
        resp = client.get("/api/technology-stack", params={"pageSize": 1})
        body = resp.json()
        if not body["data"]:
            pytest.skip("No technology-stack entries")
        assert_has_keys(body["data"][0], ["id", "component", "category", "sourceType", "source"], "tech-stack")

    def test_filter_component(self, client):
        resp = client.get("/api/technology-stack", params={"component": "Java"})
        assert resp.status_code == 200

    def test_filter_category(self, client):
        resp = client.get("/api/technology-stack", params={"category": "Backend"})
        assert resp.status_code == 200

    def test_filter_eaAdvice(self, client):
        resp = client.get("/api/technology-stack", params={"eaAdvice": "Recommended"})
        assert resp.status_code == 200

    def test_filter_status(self, client):
        resp = client.get("/api/technology-stack", params={"status": "Active"})
        assert resp.status_code == 200

    def test_sort(self, client):
        resp = client.get("/api/technology-stack", params={
            "sortField": "component", "sortOrder": "asc"
        })
        assert resp.status_code == 200

    def test_pagination_size(self, client):
        resp = client.get("/api/technology-stack", params={"page": 1, "pageSize": 3})
        body = resp.json()
        assert len(body["data"]) <= 3
