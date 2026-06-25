"""Applications list endpoint tests — Priority 1."""
import pytest
from helpers.pagination import assert_paginated, assert_has_keys


@pytest.mark.readonly
@pytest.mark.priority1
class TestApplicationsList:
    def test_list_paginated(self, client):
        resp = client.get("/api/applications")
        assert resp.status_code == 200
        body = resp.json()
        assert_paginated(body)

    def test_filter_appId(self, client):
        resp = client.get("/api/applications", params={"appId": "A"})
        assert resp.status_code == 200

    def test_filter_name(self, client):
        resp = client.get("/api/applications", params={"name": "SAP"})
        assert resp.status_code == 200
