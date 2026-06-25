"""Reports endpoint tests — Priority 3."""
import pytest
from helpers.pagination import assert_paginated


@pytest.mark.readonly
@pytest.mark.priority3
class TestReports:
    def test_lead_time_paginated(self, client):
        resp = client.get("/api/reports/lead-time")
        assert resp.status_code == 200
        body = resp.json()
        assert_paginated(body)

    def test_lead_time_filter_status(self, client):
        resp = client.get("/api/reports/lead-time", params={"status": "Completed"})
        assert resp.status_code == 200

    def test_lead_time_filter_projectId(self, client):
        resp = client.get("/api/reports/lead-time", params={"projectId": "P001"})
        assert resp.status_code == 200

    def test_lead_time_pagination(self, client):
        resp = client.get("/api/reports/lead-time", params={"page": 1, "pageSize": 5})
        body = resp.json()
        assert len(body["data"]) <= 5
