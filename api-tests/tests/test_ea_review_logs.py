"""EA Review Logs endpoint tests — Priority 3."""
import pytest
from helpers.pagination import assert_paginated


@pytest.mark.readonly
@pytest.mark.priority3
class TestEaReviewLogs:
    def test_list_paginated(self, client):
        resp = client.get("/api/ea-review-logs")
        assert resp.status_code == 200
        body = resp.json()
        assert_paginated(body)

    def test_filter_projectId(self, client):
        resp = client.get("/api/ea-review-logs", params={"projectId": "P001"})
        assert resp.status_code == 200

    def test_filter_operator(self, client):
        resp = client.get("/api/ea-review-logs", params={"operator": "admin"})
        assert resp.status_code == 200

    def test_pagination_size(self, client):
        resp = client.get("/api/ea-review-logs", params={"page": 1, "pageSize": 5})
        body = resp.json()
        assert len(body["data"]) <= 5

    def test_sort(self, client):
        resp = client.get("/api/ea-review-logs", params={
            "sortField": "createdAt", "sortOrder": "desc"
        })
        assert resp.status_code == 200
