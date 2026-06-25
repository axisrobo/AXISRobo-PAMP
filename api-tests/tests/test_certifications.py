"""Certifications endpoint tests — Priority 3."""
import pytest
from helpers.pagination import assert_paginated


@pytest.mark.readonly
@pytest.mark.priority3
class TestCertificationsList:
    def test_list_paginated(self, client):
        resp = client.get("/api/certifications")
        assert resp.status_code == 200
        body = resp.json()
        assert_paginated(body)

    def test_pagination_params(self, client):
        resp = client.get("/api/certifications", params={"page": 1, "pageSize": 5})
        body = resp.json()
        assert len(body["data"]) <= 5

    def test_filter_name(self, client):
        resp = client.get("/api/certifications", params={"name": "AWS"})
        assert resp.status_code == 200

    def test_filter_type(self, client):
        resp = client.get("/api/certifications", params={"type": "Cloud"})
        assert resp.status_code == 200

    def test_filter_itCode(self, client):
        resp = client.get("/api/certifications", params={"itCode": "TEST"})
        assert resp.status_code == 200

    def test_sort(self, client):
        resp = client.get("/api/certifications", params={
            "sortField": "name", "sortOrder": "asc"
        })
        assert resp.status_code == 200
